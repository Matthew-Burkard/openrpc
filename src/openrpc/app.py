"""Module providing RPCServer class."""

from __future__ import annotations

import asyncio
from collections import Awaitable
import logging
import traceback
from inspect import isawaitable
from pathlib import Path
from typing import Any, Callable, Union

from jsonrpcobjects.errors import (
    INTERNAL_ERROR,
    METHOD_NOT_FOUND,
    InvalidParamsError,
    MethodNotFoundError,
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
    ResponseType,
    ResultResponse,
)
from jsonrpcobjects.parse import ParseResult, parse_request
from pydantic import ValidationError
from pydantic_core import PydanticUndefined

from openrpc._common import MethodMetaData, RPCMethod
from openrpc._depends import InjectModel
from openrpc._discover import get_openrpc_doc
from openrpc._method_registrar import MethodRegistrar
from openrpc._objects import (
    CallableType,
    ContentDescriptor,
    Info,
    Method,
    ParamStructure,
    RPCPermissionError,
    Schema,
    Server,
    Tag,
)
from openrpc.context import BaseContext

__all__ = ("RPCApp",)

DEFAULT_ERROR_CODE = -32000

log = logging.getLogger("openrpc")
_META_REF = "https://raw.githubusercontent.com/open-rpc/meta-schema/master/schema.json"

AnyRequest = Union[RequestType, NotificationType]
AnyResponse = Union[ResponseType, ErrorType]

RequestHook = Callable[[AnyRequest], Awaitable[AnyRequest]]
ResponseHook = Callable[[AnyResponse], Awaitable[None]]

Params = Union[list[Any], dict[str, Any]]


class AppRouter(MethodRegistrar):
    """RPC method router."""

    def __init__(
        self, prefix: str | None = None, tags: list[Tag | str] | None = None
    ) -> None:
        """Instantiate a new method router.

        :param prefix: Prefix to add to the name of each method of this router.
        :param tags: Tags to apply to every method of this router.
        """
        self.prefix = prefix
        self.tags = tags or []
        super().__init__()


class RPCApp(MethodRegistrar):
    """OpenRPC server to register methods with."""

    def __init__(
        self,
        info: Info | None = None,
        servers: Server | list[Server] | None = None,
        *,
        debug: bool = False,
    ) -> None:
        """Instantiate an OpenRPC app object.

        :param config: Open RPC server config properties.
        :param debug: Include internal error details in error responses.
        """
        super().__init__()
        info = info or Info(title="RPC Server", version="0.1.0")
        self._routers: list[MethodRegistrar] = []
        self._request_processor.debug = debug
        # Set OpenRPC server info.
        self._debug = debug
        self.info = Info(
            title=info.title or "RPC Server", version=info.version or "0.1.0"
        )
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if info.description is not None:
            self.info.description = info.description
        if info.terms_of_service is not None:
            self.info.terms_of_service = info.terms_of_service
        if info.contact is not None:
            self.info.contact = info.contact
        if info.license_ is not None:
            self.info.license_ = info.license_
        self._servers = servers or Server(name="default", url="127.0.0.1")
        # Register discover method.
        schema = Schema()
        schema.ref = _META_REF
        _ = self.method(
            name="rpc.discover",
            params=[],
            result=ContentDescriptor(name="OpenRPC Schema", schema=schema),
        )(self.discover)

    @property
    def methods(self) -> list[Method]:
        """Get all methods of this server."""
        return get_openrpc_doc(
            self.info, self._rpc_methods.values(), self._servers
        ).methods

    def include_router(self, router: AppRouter) -> None:
        """Add a method router to this app.

        :param router: Router to add to this RPC app.
        """

        def _add_router_method(
            func: CallableType, metadata: MethodMetaData
        ) -> CallableType:
            new_data = metadata.model_copy()
            if router.prefix:
                new_data.name = f"{router.prefix}{metadata.name}"
            if router.tags:
                tag_objects = [
                    t if isinstance(t, Tag) else Tag(name=t) for t in router.tags
                ]
                if new_data.tags:
                    new_data.tags.extend(tag_objects)
                else:
                    new_data.tags = tag_objects
            return self._method(func, new_data)

        def _router_method_decorator(
            func: CallableType,
        ) -> Callable[[CallableType, MethodMetaData], CallableType]:
            def _wrapper(fun: CallableType, metadata: MethodMetaData) -> CallableType:
                _ = _add_router_method(fun, metadata)
                return func(fun, metadata)

            return _wrapper

        router._method = _router_method_decorator(router._method)  # pyright: ignore[reportAttributeAccessIssue]
        for rpc_method in router._rpc_methods.values():
            _ = _add_router_method(rpc_method.function, rpc_method.metadata)

    async def process(
        self, request: str, context: BaseContext | None = None
    ) -> str | None:
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

    async def handle_request(  # noqa: PLR0911
        self, parse_result: ParseResult, context: BaseContext | None
    ) -> str | None:
        """Handle a parsed JSON RPC request.

        :param parse_result: Parsed JSON-RPC 2.0 request.
        :param context: Context of the request.
        :return: A JSON-RPC response or None.
        """
        # `hasattr` and type ignore because python can't check `isinstance` on
        #  subscripted generics.
        if hasattr(parse_result, "error"):
            return ErrorResponse(id=None, error=parse_result.error).model_dump_json()  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
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
        parsed_request: RequestType = parse_result  # pyright: ignore[reportAssignmentType]
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
        except InvalidParamsError as e:
            return ErrorResponse(id=parse_result.id, error=e.rpc_error).model_dump_json(
                by_alias=True
            )
        except MethodNotFoundError:
            return _get_method_not_found_error(parse_result)  # pyright: ignore[reportArgumentType]
        except Exception as error:
            return _get_server_error(
                parsed_request, error, debug=self.debug
            ).model_dump_json(by_alias=True)

    async def call_method(
        self,
        method: str,
        params: Params | None = None,
        context: BaseContext | None = None,
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
        if params:
            params = self._get_validated_params(params, rpc_method)
        elif rpc_method.params_model.model_fields:
            # Get defaults in case of `Undefined` params.
            params = {
                k: v.default
                for k, v in rpc_method.params_model.model_fields.items()
                if v.default is not PydanticUndefined
            }
        params = (
            self._resovle_context(rpc_method, params, context) if context else params
        )
        params = await self._resovle_dependencies(params, rpc_method.inject, context)
        if isinstance(params, list):
            if rpc_method.metadata.param_structure is ParamStructure.BY_NAME:
                raise InvalidParamsError(data="Params must be passed by name.")
            result = rpc_method.function(*params)
        else:
            if rpc_method.metadata.param_structure is ParamStructure.BY_POSITION:
                raise InvalidParamsError(data="Params must be passed by position.")
            result = rpc_method.function(**params)
        return await result if isawaitable(result) else result

    def _get_validated_params(self, params: Params, method: RPCMethod) -> Params:
        try:
            if isinstance(params, list):
                params_dict: dict[str, Any] = {}
                for i, field_name in enumerate(method.params_model.model_fields):
                    # Params may have default values.
                    if i < len(params):
                        params_dict[field_name] = params[i]
                validated_params = method.params_model(**params_dict)
                return [
                    getattr(validated_params, field_name)
                    for field_name in type(validated_params).model_fields
                ]
            params_model = method.params_model(**params)
            return {
                field: getattr(params_model, field)
                for field in type(params_model).model_fields
            }
        except ValidationError as e:
            raise InvalidParamsError(data=str(e)) from e

    def _resovle_context(
        self, method: RPCMethod, params: Params, context: BaseContext
    ) -> Params:
        if method.context_arg is not None:
            if isinstance(params, list):
                params.insert(method.context_arg[1], context)
            else:
                params[method.context_arg[0]] = context
        return params

    async def _resovle_dependencies(
        self,
        params: Params,
        injected_params: list[InjectModel],
        context: BaseContext | None,
    ) -> Params:
        for dependency in injected_params:
            if dependency.requires_context:
                if context is None:
                    msg = (
                        f"Injected dependency {dependency.name} requires context but"
                        " none was provided. `Context` needs to be passed to"
                        " `RPCApp.process`"
                    )
                    raise ValueError(msg)
                value = dependency.function(context)  # pyright: ignore[reportCallIssue]
            else:
                value = dependency.function()  # pyright: ignore[reportCallIssue]
            if isawaitable(value):
                value = await value
            if isinstance(params, list):
                params.insert(dependency.index, value)
            else:
                params[dependency.name] = value
        return params

    def discover(self) -> dict[str, Any]:
        """Execute "rpc.discover" method defined in OpenRPC spec."""
        openrpc = get_openrpc_doc(self.info, self._rpc_methods.values(), self._servers)
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
    ).model_dump_json(by_alias=True)


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
    # Format the external traceback into a string.
    external_traceback_string = "".join(traceback.format_list(external_tb))
    exception_message = "".join(traceback.format_exception_only(type(error), error))
    return f"{external_traceback_string}{exception_message}"
