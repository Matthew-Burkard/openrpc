"""Module responsible for processing a method call."""

__all__ = ("MethodProcessor",)

import inspect
import logging
import traceback
from pathlib import Path
from typing import Any, Optional, Union

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
from openrpc._common import RPCMethod
from openrpc._objects import RPCPermissionError

log = logging.getLogger("openrpc")
by_position_error = DataError(
    code=-32602, message="Invalid params", data="Params must be passed by position."
)
by_name_error = DataError(
    code=-32602, message="Invalid params", data="Params must be passed by name."
)


class MethodProcessor:
    """Execute a method passing it a parsed JSON RPC 2.0 request."""

    def __init__(
        self,
        method: RPCMethod,
        uncaught_error_code: int,
        request: Union[RequestType, NotificationType],
        depends_values: Optional[dict[str, Any]],
        security: Optional[dict[str, list[str]]],
        *,
        debug: bool,
    ) -> None:
        """Init a MethodProcessor.

        :param method: The Python callable.
        :param uncaught_error_code: Code for errors raised by method.
        :param request: Request to execute.
        :param depends_values: Values passed to functions with dependencies.
        :param security: Scheme and scopes of method caller.
        :param debug: Include internal error details in responses.
        """
        self.debug = debug
        self.method = method
        self.request = request
        self.uncaught_error_code = uncaught_error_code
        self.depends = depends_values or {}
        self.security = security or {}

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

    async def execute_async(self) -> Any:
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
        if not self._check_permissions():
            raise RPCPermissionError()
        # If permissions are present, call method.
        params: Optional[Union[dict, list]]
        params_msg = ""
        missing_dependencies = [
            k for k in self.method.depends_params if k not in self.depends
        ]
        if missing_dependencies:
            raise AttributeError(
                "Missing dependent values %s for method [%s]"
                % (missing_dependencies, self.method.metadata.name)
            )
        dependencies = {k: self.depends.get(k) for k in self.method.depends_params}
        # Call method.
        if isinstance(self.request, (Request, Notification)):
            result = self.method.function(**dependencies)
        elif isinstance(self.request.params, list):
            if self.method.metadata.param_structure == ParamStructure.BY_NAME:
                raise InvalidParams(by_name_error)
            params = self._get_list_params(self.request.params)
            result = self.method.function(*params, **dependencies)
            params_msg = ", ".join(str(p) for p in params)
        else:
            if self.method.metadata.param_structure == ParamStructure.BY_POSITION:
                raise InvalidParams(by_position_error)
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
            raise InvalidParams(
                DataError(code=-32602, message="Invalid params", data=str(e))
            ) from e

    def _get_dict_params(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.method.params_model(**params).model_dump()
        except ValidationError as e:
            raise InvalidParams(
                DataError(code=-32602, message="Invalid params", data=str(e))
            ) from e

    def _check_permissions(self) -> bool:
        # Default to permitting if no security is set for method.
        permit = not self.method.metadata.security
        # If any scheme and scopes are matched, permit method call.
        for method_scheme, method_scopes in self.method.metadata.security.items():
            call_scopes = self.security.get(method_scheme)
            if call_scopes is None:
                continue
            if all(scope in call_scopes for scope in method_scopes):
                permit = True
        return permit


def _get_trimmed_traceback(error: Exception) -> str:
    tb = traceback.extract_tb(error.__traceback__)
    # Remove framework inner workings from traceback.
    file_path = Path(__file__).resolve()
    external_tb = [frame for frame in tb if Path(frame.filename).resolve() != file_path]

    # Format the external traceback into a string
    external_traceback_string = "".join(traceback.format_list(external_tb))
    exception_message = "".join(traceback.format_exception_only(type(error), error))
    return f"{external_traceback_string}{exception_message}"
