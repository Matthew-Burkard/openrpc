"""Module responsible for processing a method call."""

__all__ = ("MethodProcessor",)

import inspect
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, Union

from jsonrpcobjects.errors import InvalidParams, JSONRPCError
from jsonrpcobjects.objects import (
    DataError,
    Error,
    ErrorResponse,
    ErrorType,
    Notification,
    NotificationType,
    ParamsNotification,
    ParamsRequest,
    Request,
    RequestType,
    ResultResponse,
)
from pydantic import ValidationError

from openrpc import ParamStructure
from openrpc._common import RPCMethod, SecurityFunctionDetails
from openrpc._depends import DependsModel
from openrpc._objects import RPCPermissionError

log = logging.getLogger("openrpc")


class MethodProcessor:
    """Execute a method passing it a parsed JSON RPC 2.0 request."""

    def __init__(
        self,
        method: RPCMethod,
        uncaught_error_code: int,
        request: Union[RequestType, NotificationType],
        caller_details: Optional[Any],
        security: Optional[SecurityFunctionDetails],
        *,
        debug: bool,
    ) -> None:
        """Init a MethodProcessor.

        :param method: The Python callable.
        :param uncaught_error_code: Code for errors raised by method.
        :param request: Request to execute.
        :param caller_details: Values passed to functions with
            dependencies and security functions.
        :param security: Server security function details.
        :param debug: Include internal error details in responses.
        """
        self.debug = debug
        self.method = method
        self.request = request
        self.uncaught_error_code = uncaught_error_code
        self.caller_details = caller_details
        self.security = security
        self._depends: dict[Callable, Any] = {}

    def execute(self) -> Optional[str]:
        """Execute the method and get the JSON-RPC2 response."""
        try:
            result = self._execute()
            if isinstance(self.request, (Notification, ParamsNotification)):
                # If request was notification, return nothing.
                return None
            return ResultResponse(id=self.request.id, result=result).model_dump_json()

        except Exception as error:
            return self._get_error_response(error)

    async def execute_async(self) -> Optional[str]:
        """Execute the method and get the JSON-RPC2 response.

        If the method is an async method it will be awaited.
        """
        try:
            result = self._execute()
            if inspect.isawaitable(result):
                result = await result
            if isinstance(self.request, (Notification, ParamsNotification)):
                # If request was notification, return nothing.
                return None
            return ResultResponse(id=self.request.id, result=result).model_dump_json()

        except Exception as error:
            return self._get_error_response(error)

    def _execute(self) -> Any:
        # Get depends values from `Depends` functions.
        dependencies = self._resolve_depends_params(
            self.method.depends, self.caller_details
        )

        # Raise permission error if any problems with `security_scheme`.
        if error := self._get_permission_error():
            raise RPCPermissionError(error if self.debug else None)

        # If permissions are present, call method.
        params: Optional[Union[dict, list]]
        params_msg = ""

        # Call method.
        if isinstance(self.request, (Request, Notification)):
            result = self.method.function(**dependencies)
        elif isinstance(self.request.params, list):
            if self.method.metadata.param_structure == ParamStructure.BY_NAME:
                msg = "Params must be passed by name."
                raise InvalidParams(msg)
            params = self._get_list_params(self.request.params)
            result = self.method.function(*params, **dependencies)
            params_msg = ", ".join(str(p) for p in params)
        else:
            if self.method.metadata.param_structure == ParamStructure.BY_POSITION:
                msg = "Params must be passed by position."
                raise InvalidParams(msg)
            params = self._get_dict_params(self.request.params)
            result = self.method.function(**params, **dependencies)
            params_msg = ", ".join(f"{k}={v}" for k, v in params.items())

        # Logging
        id_msg = "None"
        if isinstance(self.request, (Request, ParamsRequest)):
            if isinstance(self.request.id, str):
                id_msg = f'"{self.request.id}"'
            else:
                id_msg = str(self.request.id)
        log.info("%s: %s(%s) -> %s", id_msg, self.request.method, params_msg, result)
        return result

    def _get_error_response(self, error: Exception) -> Optional[str]:
        log.exception("%s:", type(error).__name__)

        if not isinstance(self.request, (ParamsRequest, Request)):
            return None

        if isinstance(error, JSONRPCError):
            return ErrorResponse(
                id=self.request.id, error=error.rpc_error
            ).model_dump_json()

        if self.debug:
            traceback_str = _get_trimmed_traceback(error)
            error_object: ErrorType = DataError(
                code=self.uncaught_error_code,
                message="Server error",
                data=f"{type(error).__name__}\n{traceback_str}",
            )
        else:
            error_object = Error(code=self.uncaught_error_code, message="Server error")

        return ErrorResponse(id=self.request.id, error=error_object).model_dump_json()

    def _get_list_params(self, params: list[Any]) -> list[Any]:
        try:
            params_dict = {}
            for i, field_name in enumerate(self.method.params_model.model_fields):
                # Params may have default values.
                if i < len(params):
                    params_dict[field_name] = params[i]
            validated_params = self.method.params_model(**params_dict)
            return [
                getattr(validated_params, field_name)
                for field_name in validated_params.model_fields
            ]
        except ValidationError as e:
            raise InvalidParams(str(e)) from e

    def _get_dict_params(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            params_model = self.method.params_model(**params)
            return {
                field: getattr(params_model, field)
                for field in params_model.model_fields
            }
        except ValidationError as e:
            raise InvalidParams(data=str(e)) from e

    def _get_permission_error(self) -> Optional[str]:
        # Default to permitting if no security is set for method.
        permit = not self.method.metadata.security
        if permit:
            return None
        if self.security is None:
            return "No security function has been set for the RPC Server."

        # Get security function depends values.
        security_dependencies = self._resolve_depends_params(
            self.security.depends_params, self.caller_details
        )

        # Get active security scheme.
        if self.security.accepts_caller_details:
            active_scheme = self.security.function(
                self.caller_details, **security_dependencies
            )
        else:
            active_scheme = self.security.function(**security_dependencies)
        if not active_scheme:
            return "No active security schemes for caller."

        missing_scopes = {}
        # If any scheme and scopes are matched, permit method call.
        for method_scheme, method_scopes in self.method.metadata.security.items():
            call_scopes = active_scheme.get(method_scheme)
            if call_scopes is None:
                missing_scopes[method_scheme] = method_scopes
                continue
            missing_scopes[method_scheme] = [
                scope for scope in method_scopes if scope not in call_scopes
            ]
            if not missing_scopes[method_scheme]:
                return None

        # Get string describing missing scopes.
        details = "\n\t".join(
            f"{scheme}: {scopes}" for scheme, scopes in missing_scopes.items()
        )

        return f"No scheme had all scopes met by caller.\nMissing scopes:\n\t{details}"

    def _resolve_depends_params(
        self, depends_params: dict[str, DependsModel], caller_details: Any
    ) -> dict[str, Any]:
        # Resolve values of nested `Depends` parameters.
        for nested_dep in depends_params.values():
            # If this dependency value is already resolved, continue.
            if self._depends.get(nested_dep.function):
                continue
            # Resolve nested dependencies of nested dependency.
            dependency_dependencies = {}
            if nested_dep.depends_params:
                dependency_dependencies = self._resolve_depends_params(
                    nested_dep.depends_params, caller_details
                )
            # Resolve nested dependency.
            if nested_dep.accepts_caller_details:
                self._depends[nested_dep.function] = nested_dep.function(
                    caller_details, **dependency_dependencies
                )
            else:
                self._depends[nested_dep.function] = nested_dep.function(
                    **dependency_dependencies
                )

        # Return values requested now that all values needed are resoled.
        return {
            param_name: self._depends[dep.function]
            for param_name, dep in depends_params.items()
        }


def _get_trimmed_traceback(error: Exception) -> str:
    tb = traceback.extract_tb(error.__traceback__)
    # Remove framework inner workings from traceback.
    file_path = Path(__file__).resolve()
    external_tb = [frame for frame in tb if Path(frame.filename).resolve() != file_path]

    # Format the external traceback into a string
    external_traceback_string = "".join(traceback.format_list(external_tb))
    exception_message = "".join(traceback.format_exception_only(type(error), error))
    return f"{external_traceback_string}{exception_message}"
