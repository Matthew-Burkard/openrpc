"""Module responsible for processing a method call."""

__all__ = ("MethodProcessor",)

import inspect
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, Union

from jsonrpcobjects.errors import InternalError, InvalidParams, JSONRPCError
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
from pydantic_core import PydanticUndefined

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
            # Raise permission error if any problems with `security_scheme`.
            self._check_permissions()
            # Get depends values from `Depends` functions.
            dependencies = self._resolve_depends_params(
                self.method.depends, self.caller_details
            )

            # Get result.
            result = self._execute(dependencies)
            self._log_call(result)
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
            # Raise permission error if any problems with `security_scheme`.
            await self._check_permissions_async()
            # Get depends values from `Depends` functions.
            dependencies = await self._resolve_depends_params_async(
                self.method.depends, self.caller_details
            )

            # Call method and get result.
            result = self._execute(dependencies)
            if inspect.isawaitable(result):
                result = await result
            self._log_call(result)

            # Return method result.
            if isinstance(self.request, (Notification, ParamsNotification)):
                # If request was notification, return nothing.
                return None
            return ResultResponse(id=self.request.id, result=result).model_dump_json()

        except Exception as error:
            return self._get_error_response(error)

    def _execute(self, dependencies: dict[str, Any]) -> Any:
        # Call method.
        if isinstance(self.request, (Request, Notification)):
            # No params.
            defaults = {}
            if self.method.params_model.model_fields:
                # Get defaults in case of `Undefined` params.
                defaults = {
                    k: v.default
                    for k, v in self.method.params_model.model_fields.items()
                    if v.default is not PydanticUndefined
                }
            result = self.method.function(**{**dependencies, **defaults})

        elif isinstance(self.request.params, list):
            # List params.
            if self.method.metadata.param_structure == ParamStructure.BY_NAME:
                msg = "Params must be passed by name."
                raise InvalidParams(msg)
            list_params = self._get_list_params(self.request.params)
            result = self.method.function(*list_params, **dependencies)

        else:
            # Dict params.
            if self.method.metadata.param_structure == ParamStructure.BY_POSITION:
                msg = "Params must be passed by position."
                raise InvalidParams(msg)
            dict_params = self._get_dict_params(self.request.params)
            result = self.method.function(**dict_params, **dependencies)

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

    def _check_permissions(self) -> Optional[str]:
        # Default to permitting if no security is set for method.
        permit = not self.method.metadata.security
        if permit:
            return None
        if self.security is None:
            msg = "No security function has been set for the RPC Server."
            raise RPCPermissionError(msg if self.debug else None)

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

        if inspect.isawaitable(active_scheme):
            msg = "Must use `process_request_async` if security function is async."
            raise InternalError(data=msg)

        # MyPy fails to understand `inspect.isawaitable(active_scheme)`.
        error = self._get_permission_error_from_scheme(active_scheme)  # type: ignore
        if error:
            raise RPCPermissionError(error if self.debug else None)
        return None

    async def _check_permissions_async(self) -> Optional[str]:
        # Default to permitting if no security is set for method.
        permit = not self.method.metadata.security
        if permit:
            return None
        if self.security is None:
            msg = "No security function has been set for the RPC Server."
            raise RPCPermissionError(msg if self.debug else None)

        # Get security function depends values.
        security_dependencies = await self._resolve_depends_params_async(
            self.security.depends_params, self.caller_details
        )

        # Get active security scheme.
        if self.security.accepts_caller_details:
            result = self.security.function(
                self.caller_details, **security_dependencies
            )
        else:
            result = self.security.function(**security_dependencies)
        # Await result if security function is async.
        active_scheme = await result if inspect.isawaitable(result) else result

        error = self._get_permission_error_from_scheme(active_scheme)
        if error:
            raise RPCPermissionError(error if self.debug else None)
        return None

    def _get_permission_error_from_scheme(
        self, active_scheme: Optional[dict[str, list[str]]]
    ) -> Optional[str]:
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
        for dependency in depends_params.values():
            # If this dependency value is already resolved, continue.
            if self._depends.get(dependency.function):
                continue
            # Resolve nested dependencies of nested dependency.
            dependency_dependencies = {}
            if dependency.depends_params:
                dependency_dependencies = self._resolve_depends_params(
                    dependency.depends_params, caller_details
                )
            # Resolve nested dependency.
            if dependency.accepts_caller_details:
                self._depends[dependency.function] = dependency.function(
                    caller_details, **dependency_dependencies
                )
            else:
                self._depends[dependency.function] = dependency.function(
                    **dependency_dependencies
                )

        # Return values requested now that all values needed are resoled.
        return {
            param_name: self._depends[dep.function]
            for param_name, dep in depends_params.items()
        }

    async def _resolve_depends_params_async(
        self, depends_params: dict[str, DependsModel], caller_details: Any
    ) -> dict[str, Any]:
        # Resolve values of nested `Depends` parameters.
        for dependency in depends_params.values():
            # If this dependency value is already resolved, continue.
            if self._depends.get(dependency.function):
                continue
            # Resolve nested dependencies of nested dependency.
            dependency_dependencies = {}
            if dependency.depends_params:
                dependency_dependencies = await self._resolve_depends_params_async(
                    dependency.depends_params, caller_details
                )
            # Resolve nested dependency.
            if dependency.accepts_caller_details:
                result = dependency.function(caller_details, **dependency_dependencies)
            else:
                result = dependency.function(**dependency_dependencies)

            # Await result if `Depends` function is async.
            self._depends[dependency.function] = (
                await result if inspect.isawaitable(result) else result
            )

        # Return values requested now that all values needed are resoled.
        return {
            param_name: self._depends[dep.function]
            for param_name, dep in depends_params.items()
        }

    def _log_call(self, result: Any) -> None:
        """Log a method call, param, and result."""
        # Log method call, params, and result.
        if isinstance(self.request, (Request, Notification)):
            param_msg = ""
        elif isinstance(self.request.params, dict):
            param_msg = ", ".join(f"{k}={v}" for k, v in self.request.params.items())
        else:
            param_msg = ", ".join(str(p) for p in self.request.params)
        id_msg = "None"
        if isinstance(self.request, (Request, ParamsRequest)):
            if isinstance(self.request.id, str):
                id_msg = f'"{self.request.id}"'
            else:
                id_msg = str(self.request.id)
        log.info("%s: %s(%s) -> %s", id_msg, self.request.method, param_msg, result)


def _get_trimmed_traceback(error: Exception) -> str:
    tb = traceback.extract_tb(error.__traceback__)
    # Remove framework inner workings from traceback.
    file_path = Path(__file__).resolve()
    external_tb = [frame for frame in tb if Path(frame.filename).resolve() != file_path]

    # Format the external traceback into a string
    external_traceback_string = "".join(traceback.format_list(external_tb))
    exception_message = "".join(traceback.format_exception_only(type(error), error))
    return f"{external_traceback_string}{exception_message}"
