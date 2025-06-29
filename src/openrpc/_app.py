"""Module providing RPCServer class."""

from __future__ import annotations

import asyncio
import logging
import traceback
from pathlib import Path
from typing import Any, Awaitable, Callable, Union

from jsonrpcobjects.errors import INTERNAL_ERROR, METHOD_NOT_FOUND, MethodNotFoundError
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
    ResponseType,
    ResultResponse,
)
from jsonrpcobjects.parse import ParseResult, parse_request

from openrpc._common import RPCMethod
from openrpc._context import Context
from openrpc._discover import get_openrpc_doc
from openrpc._method_registrar import MethodRegistrar
from openrpc._objects import ContentDescriptor, Info, RPCPermissionError, Schema, Server

__all__ = ("RPCApp",)

DEFAULT_ERROR_CODE = -32000

log = logging.getLogger("openrpc")
_META_REF = "https://raw.githubusercontent.com/open-rpc/meta-schema/master/schema.json"

AnyRequest = Union[RequestType, NotificationType]
AnyResponse = Union[ResponseType, ErrorType]

RequestHook = Callable[[AnyRequest], Awaitable[AnyRequest]]
ResponseHook = Callable[[AnyResponse], Awaitable[None]]

Params = Union[list[Any], dict[str, Any]]


class RPCApp(MethodRegistrar):
    """OpenRPC server to register methods with."""

    def __init__(
        self,
        config: Info | None = None,
        servers: Server | list[Server] | None = None,
        *,
        debug: bool = False,
    ) -> None:
        """Instantiate an OpenRPC app object.

        :param config: Open RPC server config properties.
        :param debug: Include internal error details in error responses.
        """
        super().__init__()
        config = config or Info(title="RPC Server", version="0.1.0")
        self._routers: list[MethodRegistrar] = []
        self._request_processor.debug = debug
        # Set OpenRPC server info.
        self._debug = debug
        self._info = Info(
            title=config.title or "RPC Server", version=config.version or "0.1.0"
        )
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if config.description is not None:
            self._info.description = config.description
        if config.terms_of_service is not None:
            self._info.terms_of_service = config.terms_of_service
        if config.contact is not None:
            self._info.contact = config.contact
        if config.license_ is not None:
            self._info.license_ = config.license_
        self._servers = servers or Server(name="default", url="127.0.0.1")
        # Register discover method.
        schema = Schema()
        schema.ref = _META_REF
        self.method(
            name="rpc.discover",
            params=[],
            result=ContentDescriptor(name="OpenRPC Schema", schema=schema),
        )(self.discover)

    async def process(self, request: str, context: Context) -> str | None:
        """Process a JSON-RPC2 request.

        :param request: JSON-RPC request string.
        :param context: Additional request data.
        :return: The JSON-RPC response string.
        """
        try:
            log.debug("Processing request: %s", request)
            parsed_request = parse_request(request, debug=self.debug)
            if isinstance(parsed_request, list):
                results = await asyncio.gather(
                    *(self.handle_request(it, context) for it in parsed_request)
                )
                response = f"[{','.join(r for r in results if r is not None)}]"
            else:
                response = await self.handle_request(parsed_request, context)
        except Exception as error:
            return self._get_error_response(error).model_dump_json()
        else:
            return response

    # This exists in addition to `process` so that this can be easily overridden.
    async def handle_request(  # noqa: PLR0911
        self, parse_result: ParseResult, context: Context
    ) -> str | None:
        """Handle a parsed JSON RPC request.

        :param parse_result: Parsed JSON-RPC 2.0 request.
        :param context: Context of the request.
        :return: A JSON-RPC response or None.
        """
        # `hasattr` and type ignore because python can't check `isinstance` on
        #  subscripted generics.
        if hasattr(parse_result, "error"):
            return ErrorResponse(id=None, error=parse_result.error).model_dump_json()  # type: ignore
        if isinstance(parse_result, (ParamsNotification, Notification)):
            try:
                if isinstance(parse_result, Notification):
                    await self.call_method(parse_result.method, [], context)
                else:
                    await self.call_method(
                        parse_result.method, parse_result.params, context
                    )
            except Exception:
                return None
            else:
                return None

        # Type ignore because pyright fails to infer type.
        parsed_request: RequestType = parse_result  # type: ignore
        result: Any | None = None
        try:
            if isinstance(parse_result, ParamsRequest):
                result = await self.call_method(
                    parse_result.method, parse_result.params, context
                )
            elif isinstance(parse_result, Request):
                result = await self.call_method(parse_result.method, [], context)
            return ResultResponse(id=parsed_request.id, result=result).model_dump_json(
                by_alias=True
            )
        except MethodNotFoundError:
            return _get_method_not_found_error(parse_result)  # type: ignore
        except Exception as error:
            return _get_server_error(
                parsed_request, error, debug=self.debug
            ).model_dump_json(by_alias=True)

    async def call_method(
        self,
        method: str,
        params: Params | None = None,
        context: Context | None = None,
    ) -> Any:
        """Call a method by name with given params and context.

        :param method: Name of method to call.
        :param params: Parameters to pass to the method.
        :param context: Request context.
        :return: The result of the method call.
        """
        params = params or []
        if not (rpc_method := self._rpc_methods.get(method)):
            raise MethodNotFoundError()
        if rpc_method.metadata.scopes:
            required = rpc_method.metadata.scopes
            scopes = context.scopes if context else []
            missing = [scope for scope in required if scope not in scopes]
            if missing:
                if self.debug:
                    msg = f"Request scopes {scopes} is missing scopes {missing}"
                    raise RPCPermissionError(msg)
                raise MethodNotFoundError()
        params = (
            self._resovle_context(rpc_method, params, context) if context else params
        )
        if isinstance(params, list):
            return await rpc_method.function(*params)
        return await rpc_method.function(**params)

    def _resovle_context(
        self, method: RPCMethod, params: Params, context: Context
    ) -> Params:
        if method.context_arg is not None:
            if isinstance(params, list):
                params.insert(method.context_arg[1], context)
            else:
                params[method.context_arg[0]] = context
        return params

    def discover(self) -> dict[str, Any]:
        """Execute "rpc.discover" method defined in OpenRPC spec."""
        openrpc = get_openrpc_doc(self._info, self._rpc_methods.values(), self._servers)
        return openrpc.model_dump(by_alias=True, exclude_unset=True)

    def _get_error_response(self, error: Exception) -> ErrorResponse:
        log.exception("%s:", type(error).__name__)
        if self._debug:
            error_dict = INTERNAL_ERROR.model_dump()
            error_dict["data"] = f"{type(error).__name__}: {error}"
            error_object: Error | DataError = DataError(**error_dict)
        else:
            error_object = Error(**INTERNAL_ERROR.model_dump())
        return ErrorResponse(id=None, error=error_object)


def _get_method_not_found_error(request: RequestType) -> str | None:
    return ErrorResponse(
        id=request.id,
        error=DataError(
            code=METHOD_NOT_FOUND.code,
            message=METHOD_NOT_FOUND.message,
            data=request.method,
        ),
    ).model_dump_json()


def _get_server_error(
    request: RequestType, error: Exception, *, debug: bool
) -> ErrorResponse:
    if debug:
        error_object: ErrorType = DataError(
            code=DEFAULT_ERROR_CODE,
            message="Server error",
            data=f"{type(error).__name__}\n{_get_trimmed_traceback(error)}",
        )
    else:
        error_object = Error(code=DEFAULT_ERROR_CODE, message="Server error")
    return ErrorResponse(id=request.id, error=error_object)


def _get_trimmed_traceback(error: Exception) -> str:
    tb = traceback.extract_tb(error.__traceback__)
    # Remove framework inner workings from traceback.
    file_path = Path(__file__).resolve()
    external_tb = [frame for frame in tb if Path(frame.filename).resolve() != file_path]
    # Format the external traceback into a string
    external_traceback_string = "".join(traceback.format_list(external_tb))
    exception_message = "".join(traceback.format_exception_only(type(error), error))
    return f"{external_traceback_string}{exception_message}"
