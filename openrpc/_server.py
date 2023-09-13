"""Module providing RPCServer class."""

__all__ = ("RPCServer",)

import logging
from typing import Any, Callable, Optional, Union

from jsonrpcobjects.errors import INTERNAL_ERROR
from jsonrpcobjects.objects import DataError, Error, ErrorResponse

from openrpc import RPCRouter
from openrpc._common import MethodMetaData
from openrpc._method_registrar import CallableType, MethodRegistrar
from openrpc._objects import (
    APIKeyAuth,
    BearerAuth,
    Contact,
    ContentDescriptor,
    Info,
    License,
    Method,
    OAuth2,
    Schema,
    Server,
    Tag,
)
from ._discover.discover import get_openrpc_doc

log = logging.getLogger("openrpc")
_META_REF = "https://raw.githubusercontent.com/open-rpc/meta-schema/master/schema.json"


class RPCServer(MethodRegistrar):
    """OpenRPC server to register methods with."""

    def __init__(
        self,
        title: Optional[str] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Contact] = None,
        license_: Optional[License] = None,
        servers: Optional[Union[list[Server], Server]] = None,
        security_schemes: Optional[
            dict[str, Union[OAuth2, BearerAuth, APIKeyAuth]]
        ] = None,
        *,
        debug: bool = False,
    ) -> None:
        """Init an OpenRPC server.

        :param title: OpenRPC title.
        :param version: API version.
        :param description: Description of the app.
        :param terms_of_service: App terms of service.
        :param contact: Contact information.
        :param license_: App license.
        :param servers: Servers hosting this RPC API.
        :param security_schemes: Security schemes used by this RPC API.
        :param debug: Include internal error details in responses.
        """
        super().__init__()
        self._routers: list[MethodRegistrar] = []
        self._request_processor.debug = debug
        # Set OpenRPC server info.
        self._debug = debug
        self._info = Info(title=title or "RPC Server", version=version or "0.1.0")
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if description is not None:
            self._info.description = description
        if terms_of_service is not None:
            self._info.terms_of_service = terms_of_service
        if contact is not None:
            self._info.contact = contact
        if license_ is not None:
            self._info.license_ = license_
        self._servers = servers or Server(name="default", url="localhost")
        self.security_schemes = security_schemes
        # Register discover method.
        schema = Schema()
        schema.ref = _META_REF
        self.method(
            name="rpc.discover",
            params=[],
            result=ContentDescriptor(name="OpenRPC Schema", schema=schema),
        )(self.discover)

    @property
    def title(self) -> str:
        """Title of the application."""
        return self._info.title

    @title.setter
    def title(self, title: str) -> None:
        self._info.title = title

    @property
    def version(self) -> str:
        """Version of the OpenRPC document."""
        return self._info.version

    @version.setter
    def version(self, version: str) -> None:
        self._info.version = version

    @property
    def description(self) -> Optional[str]:
        """Verbose description of the application."""
        return self._info.description

    @description.setter
    def description(self, description: str) -> None:
        self._info.description = description

    @property
    def terms_of_service(self) -> Optional[str]:
        """URL to the Terms of Service for the API."""
        return self._info.terms_of_service

    @terms_of_service.setter
    def terms_of_service(self, terms_of_service: str) -> None:
        self._info.terms_of_service = terms_of_service

    @property
    def contact(self) -> Optional[Contact]:
        """Contact information for the exposed API."""
        return self._info.contact

    @contact.setter
    def contact(self, contact: Contact) -> None:
        self._info.contact = contact

    @property
    def license_(self) -> Optional[License]:
        """License information for the exposed API."""
        return self._info.license_

    @license_.setter
    def license_(self, license_: License) -> None:
        self._info.license_ = license_

    @property
    def servers(self) -> Union[list[Server], Server]:
        """Server Objects, which provide connectivity information to a target server."""
        return self._servers

    @servers.setter
    def servers(self, servers: Union[list[Server], Server]) -> None:
        self._servers = servers

    @property
    def default_error_code(self) -> int:
        """JSON-RPC error code used when a method raises an error."""
        return self._request_processor.uncaught_error_code

    @default_error_code.setter
    def default_error_code(self, default_error_code: int) -> None:
        self._request_processor.uncaught_error_code = default_error_code

    @property
    def methods(self) -> list[Method]:
        """Get all methods of this server."""
        return get_openrpc_doc(
            self._info, self._rpc_methods.values(), self._servers
        ).methods

    @property
    def debug(self) -> bool:
        """Include internal error details in responses if True."""
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._request_processor.debug = debug
        self._debug = debug
        for router in self._routers:
            router.debug = debug

    def include_router(
        self,
        router: RPCRouter,
        prefix: Optional[str] = None,
        tags: Optional[list[Union[Tag, str]]] = None,
    ) -> None:
        """Add an RPC method router to this server.

        :param router: Router to add to this server.
        :param prefix: Prefix to add to method names in this router.
        :param tags: Tags to add to methods in this router.
        :return: None.
        """

        def _add_router_method(
            func: CallableType, metadata: MethodMetaData
        ) -> CallableType:
            new_data = metadata.model_copy()
            if prefix:
                new_data.name = f"{prefix}{metadata.name}"
            if tags:
                tag_objects = [t if isinstance(t, Tag) else Tag(name=t) for t in tags]
                if new_data.tags:
                    new_data.tags.extend(tag_objects)
                else:
                    new_data.tags = tag_objects
            return self._method(func, new_data)

        def _router_method_decorator(
            func: CallableType,
        ) -> Callable[[CallableType, MethodMetaData], CallableType]:
            def _wrapper(fun: CallableType, metadata: MethodMetaData) -> CallableType:
                _add_router_method(fun, metadata)
                return func(fun, metadata)

            return _wrapper

        def _router_remove_partial(method: str) -> None:
            self.remove(f"{prefix}{method}") if prefix else self.remove(method)
            router._rpc_methods.pop(method)
            router._request_processor.methods.pop(method)

        for rpc_method in router._rpc_methods.values():
            _add_router_method(rpc_method.function, rpc_method.metadata)
        router._method = _router_method_decorator(router._method)  # type: ignore
        router.remove = _router_remove_partial  # type: ignore
        router.debug = self.debug
        self._routers.append(router)

    def process_request(
        self,
        data: Union[bytes, str],
        depends: Optional[dict[str, Any]] = None,
        security: Optional[dict[str, list[str]]] = None,
    ) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :param depends: Values passed to functions with dependencies.
            Values will be passed if the keyname matches the arg name
            that is a dependency.
        :param security: Scheme and scopes of method caller.
        :return: A JSON-RPC2 response or None if the request was a
            notification.
        """
        try:
            log.debug("Processing request: %s", data)
            resp = self._request_processor.process(data, depends, security)
            if resp:
                log.debug("Responding: %s", resp)
        except Exception as error:
            return self._get_error_response(error).model_dump_json()
        else:
            return resp

    async def process_request_async(
        self,
        data: Union[bytes, str],
        depends: Optional[dict[str, Any]] = None,
        security: Optional[dict[str, list[str]]] = None,
    ) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :param depends: Values passed to functions with dependencies.
            Values will be passed if the keyname matches the arg name
            that is a dependency.
        :param security: Scheme and scopes of method caller.
        :return: A JSON-RPC2 response or None if the request was a
            notification.
        """
        try:
            log.debug("Processing request: %s", data)
            resp = await self._request_processor.process_async(data, depends, security)
            if resp:
                log.debug("Responding: %s", resp)
        except Exception as error:
            return self._get_error_response(error).model_dump_json()
        else:
            return resp

    def discover(self) -> dict[str, Any]:
        """Execute "rpc.discover" method defined in OpenRPC spec."""
        openrpc = get_openrpc_doc(self._info, self._rpc_methods.values(), self._servers)
        model_dump = openrpc.model_dump(by_alias=True, exclude_unset=True)
        if self.security_schemes and openrpc.components:
            # This is done after OpenRPC model dump rather than before
            # so the security model default values will be kept,
            # `exclude_unset=True` in doc dump would remove them.
            model_dump["components"]["x-securitySchemes"] = {
                name: model.model_dump(exclude_none=True, by_alias=True)
                for name, model in self.security_schemes.items()
            }
        return model_dump

    def _get_error_response(self, error: Exception) -> ErrorResponse:
        log.exception("%s:", type(error).__name__)
        if self._debug:
            error_object: Union[Error, DataError] = DataError(
                **{
                    **INTERNAL_ERROR.model_dump(),
                    **{"data": f"{type(error).__name__}: {error}"},
                }
            )
        else:
            error_object = Error(**INTERNAL_ERROR.model_dump())
        return ErrorResponse(id=None, error=error_object)
