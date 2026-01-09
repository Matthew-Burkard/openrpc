"""Module responsible for parsing JSON RPC 2.0 requests."""

from __future__ import annotations

__all__ = ("RequestProcessor",)

import asyncio
import inspect
import logging
import traceback
from collections import Mapping
from pathlib import Path
from typing import Any, Callable

from jsonrpcobjects.errors import (
    METHOD_NOT_FOUND,
    InternalError,
    InvalidParamsError,
    JSONRPCError,
)
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
from jsonrpcobjects.parse import parse_request
from pydantic import ValidationError
from pydantic_core import PydanticUndefined

from openrpc._common import RPCMethod, SecurityFunctionDetails
from openrpc._depends import DependsModel
from openrpc._objects import ParamStructure, RPCPermissionError
from openrpc._error import OpenRPCError

log = logging.getLogger("openrpc")

NotificationTypes = (Notification, ParamsNotification)
RequestTypes = (Request, ParamsRequest)
_DEFAULT_ERROR_CODE = -32000


class RequestProcessor:
    """Class to parse requests and pass results to MethodProcessor."""

    def __init__(self, *, debug: bool) -> None:
        """Init a RequestProcessor.

        :param debug: Include internal error details in responses.
        """
        self.debug = debug
        self.methods: dict[str, RPCMethod] = {}
        self.uncaught_error_code = _DEFAULT_ERROR_CODE

    def method(self, function: RPCMethod, method_name: str) -> None:
        """Register a method with this server for later calls.

        :param function: Function to call for this method.
        :param method_name: Name of the RPC method.
        :return: None.
        """
        self.methods[method_name] = function

    def process(
        self,
        data: bytes | str,
        caller_details: Any | None,
        security: SecurityFunctionDetails | None,
    ) -> str | None:
        """Parse a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :param caller_details: Values passed to functions with
            dependencies and security schemes.
        :param security: Server security function details.
        :return: A valid JSON-RPC2 response.
        """
        parsed_request = parse_request(data, debug=self.debug)
        if isinstance(parsed_request, ErrorResponse):
            return parsed_request.model_dump_json()

        # Batch
        if isinstance(parsed_request, list):
            results: list[str] = []
            for req in parsed_request:
                if isinstance(req, ErrorResponse):
                    results.append(req.model_dump_json())
                    continue
                if req.method not in self.methods:
                    if isinstance(req, (Request, ParamsRequest)):
                        results.append(_get_method_not_found_error(req))
                    continue

                resp = MethodProcessor(
                    self.methods[req.method],
                    self.uncaught_error_code,
                    req,
                    caller_details,
                    security,
                    debug=self.debug,
                ).execute()
                # If resp is None, request is a notification.
                if resp is not None:
                    results.append(resp)
            return f"[{','.join(results)}]"

        # Single Request
        if parsed_request.method not in self.methods:
            if isinstance(parsed_request, (Request, ParamsRequest)):
                return _get_method_not_found_error(parsed_request)
            return None
        result = MethodProcessor(
            self.methods[parsed_request.method],
            self.uncaught_error_code,
            parsed_request,
            caller_details,
            security,
            debug=self.debug,
        ).execute()
        return None if isinstance(parsed_request, NotificationTypes) else result

    async def process_async(
        self,
        data: bytes | str,
        caller_details: Any | None,
        security: SecurityFunctionDetails | None,
    ) -> str | None:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :param caller_details: Values passed to functions with
            dependencies and security schemes.
        :param security: Server security function details.
        :return: A valid JSON-RPC2 response.
        """
        parsed_request = parse_request(data, debug=self.debug)
        if isinstance(parsed_request, ErrorResponse):
            return parsed_request.model_dump_json()

        # Batch
        if isinstance(parsed_request, list):

            async def _process_request(
                request: ErrorResponse | NotificationType | RequestType,
            ) -> Any:
                if isinstance(request, ErrorResponse):
                    return request.model_dump_json()
                if request.method not in self.methods:
                    if isinstance(request, (Request, ParamsRequest)):
                        return _get_method_not_found_error(request)
                    return None

                method = self.methods[request.method]
                method_result = await MethodProcessor(
                    method,
                    self.uncaught_error_code,
                    request,
                    caller_details,
                    security,
                    debug=self.debug,
                ).execute_async()
                if isinstance(request, RequestTypes):
                    return method_result
                return None

            results = await asyncio.gather(
                *[_process_request(it) for it in parsed_request]
            )
            return f"[{','.join(str(r) for r in results if r is not None)}]"

        # Single Request
        if parsed_request.method not in self.methods:
            if isinstance(parsed_request, (Request, ParamsRequest)):
                return _get_method_not_found_error(parsed_request)
            return None
        result = await MethodProcessor(
            self.methods[parsed_request.method],
            self.uncaught_error_code,
            parsed_request,
            caller_details,
            security,
            debug=self.debug,
        ).execute_async()

        return None if isinstance(parsed_request, NotificationTypes) else result


class MethodProcessor:
    """Execute a method passing it a parsed JSON RPC 2.0 request."""

    def __init__(  # noqa: PLR0913
        self,
        method: RPCMethod,
        uncaught_error_code: int,
        request: RequestType | NotificationType,
        caller_details: Any | None,
        security: SecurityFunctionDetails | None,
        *,
        debug: bool,
    ) -> None:
        """Instantiate a `MethodProcessor`.

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
        self._depends: dict[Callable[..., Any], Any] = {}

    def execute(self) -> str | None:
        """Execute the method and get the JSON-RPC2 response."""
        try:
            # Raise permission error if any problems with `security_scheme`.
            _ = self._check_permissions()
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
            return ResultResponse(id=self.request.id, result=result).model_dump_json(
                by_alias=True
            )

        except Exception as error:
            return self._get_error_response(error)

    async def execute_async(self) -> str | None:
        """Execute the method and get the JSON-RPC2 response.

        If the method is an async method it will be awaited.
        """
        try:
            # Raise permission error if any problems with `security_scheme`.
            _ = await self._check_permissions_async()
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
            return ResultResponse(id=self.request.id, result=result).model_dump_json(
                by_alias=True
            )
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
                raise InvalidParamsError(msg)
            list_params = self._get_list_params(self.request.params)
            result = self.method.function(*list_params, **dependencies)

        else:
            # Dict params.
            if self.method.metadata.param_structure == ParamStructure.BY_POSITION:
                msg = "Params must be passed by position."
                raise InvalidParamsError(msg)
            dict_params = self._get_dict_params(self.request.params)
            result = self.method.function(**dict_params, **dependencies)

        return result

    def _get_error_response(self, error: Exception) -> str | None:
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
        elif isinstance(error, OpenRPCError):
            error_object = (
                DataError(code=error.code, message=error.message, data=error.data)
                if error.data
                else Error(code=error.code, message=error.message)
            )
            return ErrorResponse(
                id=self.request.id, error=error_object
            ).model_dump_json()
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
                for field_name in type(validated_params).model_fields
            ]
        except ValidationError as e:
            raise InvalidParamsError(str(e)) from e

    def _get_dict_params(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            params_model = self.method.params_model(**params)
            return {
                field: getattr(params_model, field)
                for field in type(params_model).model_fields
            }
        except ValidationError as e:
            raise InvalidParamsError(data=str(e)) from e

    def _check_permissions(self) -> str | None:
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

        error = self._get_permission_error_from_scheme(active_scheme)
        if error:
            raise RPCPermissionError(error if self.debug else None)
        return None

    async def _check_permissions_async(self) -> str | None:
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
        self, active_scheme: Mapping[str, list[str]] | None
    ) -> str | None:
        if not active_scheme:
            return "No active security schemes for caller."

        missing_scopes: dict[str, list[str]] = {}
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


def _get_method_not_found_error(req: NotificationType | RequestType) -> str:
    return ErrorResponse(
        id=None if isinstance(req, NotificationTypes) else req.id,
        error=DataError(
            code=METHOD_NOT_FOUND.code,
            message=METHOD_NOT_FOUND.message,
            data=req.method,
        ),
    ).model_dump_json()
