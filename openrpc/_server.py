"""Module providing RPCServer class."""
import logging
from typing import Any, Callable, Optional, Union

from jsonrpcobjects.errors import INTERNAL_ERROR
from jsonrpcobjects.objects import ErrorObjectData

from openrpc import RPCRouter
from openrpc._discover import DiscoverHandler
from openrpc._method_registrar import CallableType, MethodMetaData, MethodRegistrar
from openrpc._objects import (
    ContactObject,
    ContentDescriptorObject,
    InfoObject,
    LicenseObject,
    MethodObject,
    SchemaObject,
    TagObject,
)

__all__ = ("RPCServer",)

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
        contact: Optional[ContactObject] = None,
        license_: Optional[LicenseObject] = None,
    ) -> None:
        """Init an OpenRPC server.

        :param title: OpenRPC title.
        :param version: API version.
        :param description: Description of the app.
        :param terms_of_service: App terms of service.
        :param contact: Contact information.
        :param license_: App license.
        """
        super().__init__()
        # Set OpenRPC server info.
        kwargs = {
            "title": title or "RPC Server",
            "version": version or "0.1.0",
            "description": description,
            "termsOfService": terms_of_service,
            "contact": contact,
            "license": license_,
        }
        self._info = InfoObject(**{k: v for k, v in kwargs.items() if v is not None})
        # Register discover method.
        self.method(
            name="rpc.discover",
            params=[],
            result=ContentDescriptorObject(
                name="OpenRPC Schema", schema=SchemaObject(**{"$ref": _META_REF})
            ),
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
    def contact(self) -> Optional[ContactObject]:
        """Contact information for the exposed API."""
        return self._info.contact

    @contact.setter
    def contact(self, contact: ContactObject) -> None:
        self._info.contact = contact

    @property
    def license_(self) -> Optional[LicenseObject]:
        """License information for the exposed API."""
        return self._info.license_

    @license_.setter
    def license_(self, license_: LicenseObject) -> None:
        self._info.license_ = license_

    @property
    def default_error_code(self) -> int:
        """JSON-RPC error code used when a method raises an error."""
        return self._method_processor.uncaught_error_code

    @default_error_code.setter
    def default_error_code(self, default_error_code: int) -> None:
        self._method_processor.uncaught_error_code = default_error_code

    @property
    def methods(self) -> list[MethodObject]:
        """Get all methods of this server."""
        return DiscoverHandler(self._info, self._rpc_methods.values()).execute().methods

    def include_router(
        self,
        router: RPCRouter,
        prefix: Optional[str] = None,
        tags: Optional[list[TagObject]] = None,
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
            new_data = metadata.copy()
            if prefix:
                new_data.name = f"{prefix}{metadata.name}"
            if tags:
                if new_data.tags:
                    new_data.tags.extend(tags)
                else:
                    new_data.tags = tags
            return self._method(func, new_data)

        def _router_method_decorator(
            func: CallableType,
        ) -> Callable[[CallableType, MethodMetaData], CallableType]:
            def _wrapper(fun: CallableType, metadata: MethodMetaData) -> CallableType:
                _add_router_method(fun, metadata)
                return func(fun, metadata)

            return _wrapper

        def _router_remove_partial(method: str) -> None:
            if prefix:
                self.remove(f"{prefix}{method}")
            else:
                self.remove(method)
            router._rpc_methods.pop(method)
            router._method_processor.methods.pop(method)

        for rpc_method in router._rpc_methods.values():
            _add_router_method(rpc_method.function, rpc_method.metadata)
        router._method = _router_method_decorator(router._method)  # type: ignore
        router.remove = _router_remove_partial  # type: ignore

    def process_request(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        try:
            log.debug("Processing request: %s", data)
            resp = self._method_processor.process(data)
            if resp:
                log.debug("Responding: %s", resp)
            return resp
        except Exception as error:
            log.exception("%s:", type(error).__name__)
            error_object = ErrorObjectData(**INTERNAL_ERROR.dict())
            error_object.data = f"{type(error).__name__}: {', '.join(error.args)}"
            return error_object.json()

    async def process_request_async(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        try:
            log.debug("Processing request: %s", data)
            resp = await self._method_processor.process_async(data)
            if resp:
                log.debug("Responding: %s", resp)
            return resp
        except Exception as error:
            log.exception("%s:", type(error).__name__)
            error_object = ErrorObjectData(**INTERNAL_ERROR.dict())
            error_object.data = f"{type(error).__name__}: {', '.join(error.args)}"
            return error_object.json()

    def discover(self) -> dict[str, Any]:
        """Execute "rpc.discover" method defined in OpenRPC spec."""
        return (
            DiscoverHandler(self._info, self._rpc_methods.values())
            .execute()
            .dict(by_alias=True, exclude_unset=True, exclude_none=True)
        )
