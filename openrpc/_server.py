"""Provides RPCServer class."""
import logging
from functools import partial
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
)

from jsonrpcobjects.errors import INTERNAL_ERROR
from jsonrpcobjects.objects import ErrorObjectData

from openrpc._discover import DiscoverHandler
from openrpc._method_processor import MethodProcessor
from openrpc._objects import (
    ContactObject,
    ContentDescriptorObject,
    ErrorObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    InfoObject,
    LicenseObject,
    LinkObject,
    MethodObject,
    ParamStructure,
    SchemaObject,
    ServerObject,
    TagObject,
)
from openrpc._util import Function

__all__ = ("RPCServer",)

T = TypeVar("T", bound=Callable)
C = TypeVar("C", bound=Callable)
log = logging.getLogger("openrpc")
_META_REF = "https://raw.githubusercontent.com/open-rpc/meta-schema/master/schema.json"


class RPCServer:
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
        self._method_processor = MethodProcessor()
        kwargs = {
            "title": title or "RPC Server",
            "version": version or "0.1.0",
            "description": description,
            "termsOfService": terms_of_service,
            "contact": contact,
            "license": license_,
        }
        self._info = InfoObject(**{k: v for k, v in kwargs.items() if v is not None})
        self._functions: dict[str, Function] = {}
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
        return DiscoverHandler(self._info, self._functions.values()).execute().methods

    def method(
        self,
        *args: T,
        name: Optional[str] = None,
        params: Optional[list[ContentDescriptorObject]] = None,
        result: Optional[ContentDescriptorObject] = None,
        tags: Optional[list[TagObject]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        external_docs: Optional[ExternalDocumentationObject] = None,
        deprecated: Optional[bool] = None,
        servers: Optional[list[ServerObject]] = None,
        errors: Optional[list[ErrorObject]] = None,
        links: Optional[list[LinkObject]] = None,
        param_structure: Optional[ParamStructure] = None,
        examples: Optional[list[ExamplePairingObject]] = None,
    ) -> Union[T, Callable[[C], C]]:
        """Register a method with this OpenRPC server.

        Can be used as a plain decorator, eg:

        .. code-block:: python

            @method
            def my_func()

        Or additional method info can be provided with a MethodObject:

        .. code-block:: python

            @method(name="dot.case.method", deprecated=True)
            def my_func()

        :param args: The method if this is used as a plain decorator.
        :param name: The canonical name for the method.
        :param params: A list of parameters that are applicable for this
            method.
        :param result: The description of the result returned by the
            method.
        :param tags: A list of tags for API documentation control.
        :param summary: A short summary of what the method does.
        :param description: A verbose explanation of the method
            behavior.
        :param external_docs: Additional external documentation for this
            method.
        :param deprecated: Declares this method to be deprecated.
        :param servers: An alternative servers array to service this
            method.
        :param errors: A list of custom application defined errors that
            MAY be returned.
        :param links: A list of possible links from this method call.
        :param param_structure: The expected format of the parameters
        :param examples: Array of Example Pairing Objects.
        :return: The method decorator.
        """
        metadata = {
            "name": name,
            "params": params,
            "result": result,
            "tags": tags,
            "summary": summary,
            "description": description,
            "externalDocs": external_docs,
            "deprecated": deprecated,
            "servers": servers,
            "errors": errors,
            "links": links,
            "paramStructure": param_structure,
            "examples": examples,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        if args:
            func = args[0]
        else:
            return partial(self.method, **metadata)  # type: ignore
        name = name or func.__name__
        metadata["name"] = name
        self._functions[name] = Function(function=func, metadata=metadata)
        log.debug("Registering method [%s]", func.__name__)
        return self._method_processor.method(func, name)

    def remove(self, method: str) -> None:
        """Remove a method from this server by name."""
        self._functions.pop(method)

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
            DiscoverHandler(self._info, self._functions.values())
            .execute()
            .dict(by_alias=True, exclude_unset=True, exclude_none=True)
        )
