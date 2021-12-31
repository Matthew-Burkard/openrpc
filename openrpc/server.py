"""Provides OpenRPCServer class."""
import inspect
import logging
import re
from typing import (
    Any,
    Callable,
    get_args,
    get_origin,
    get_type_hints,
    Optional,
    Type,
    Union,
)

from openrpc._method_processor import MethodProcessor
from openrpc.objects import (
    ComponentsObject,
    ContactObject,
    ContentDescriptorObject,
    ErrorObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    InfoObject,
    LicenseObject,
    LinkObject,
    MethodObject,
    OpenRPCObject,
    ParamStructure,
    SchemaObject,
    ServerObject,
    TagObject,
)

__all__ = ("RPCServer",)

T = Type[Callable]
log = logging.getLogger("openrpc")
_DEFAULT_ERROR_CODE = -32000


class RPCServer:
    """OpenRPC server to register methods with."""

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        title: str,
        version: str,
        description: Optional[str] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[ContactObject] = None,
        license: Optional[LicenseObject] = None,
    ) -> None:
        # This class wraps RPCServer which registers and executes methods.
        self._mp = MethodProcessor(_DEFAULT_ERROR_CODE)
        self._info = InfoObject(
            title=title,
            version=version,
            description=description,
            termsOfService=terms_of_service,
            contact=contact,
            license=license,
        )
        self._components: ComponentsObject = ComponentsObject(schemas={})
        self._mp.method(self.discover, method=MethodObject(name="rpc.discover"))

    def method(
        self,
        func: T,
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
    ) -> T:
        """Register a method with this OpenRPC server.

        Can be used as a plain decorator, eg:

        .. code-block::

            @method
            def my_func()

        Or additional method info can be provided with a MethodObject:

        .. code-block::

            @method(method=MethodObject(deprecated=True))
            def my_func()

        :param func: The method if this is used as a plain decorator.
        :param name: TODO
        :param params: TODO
        :param result: TODO
        :param tags: TODO
        :param summary: TODO
        :param description: TODO
        :param external_docs: TODO
        :param deprecated: TODO
        :param servers: TODO
        :param errors: TODO
        :param links: TODO
        :param param_structure: TODO
        :param examples: TODO
        :return: The decorated method.
        """
        method = MethodObject(
            name=name,
            params=params,
            result=result,
            tags=tags,
            summary=summary,
            description=description,
            externalDocs=external_docs,
            deprecated=deprecated,
            servers=servers,
            errors=errors,
            links=links,
            paramStructure=param_structure,
            examples=examples,
        )
        return self._mp.method(func, method)

    @property
    def title(self) -> str:
        """TODO title doc."""
        return self._info.title

    @title.setter
    def title(self, title: str) -> None:
        self._info.title = title

    @property
    def version(self) -> str:
        """TODO version doc."""
        return self._info.version

    @version.setter
    def version(self, version: str) -> None:
        self._info.version = version

    @property
    def description(self) -> str:
        """TODO description doc."""
        return self._info.description

    @description.setter
    def description(self, description: str) -> None:
        self._info.description = description

    @property
    def terms_of_service(self) -> str:
        """TODO terms_of_service doc."""
        return self._info.terms_of_service

    @terms_of_service.setter
    def terms_of_service(self, terms_of_service: str) -> None:
        self._info.terms_of_service = terms_of_service

    @property
    def contact(self) -> ContactObject:
        """TODO contact doc."""
        return self._info.contact

    @contact.setter
    def contact(self, contact: ContactObject) -> None:
        self._info.contact = contact

    @property
    def license(self) -> LicenseObject:
        """TODO license doc."""
        return self._info.license

    # noinspection PyShadowingBuiltins
    @license.setter
    def license(self, license: LicenseObject) -> None:
        self._info.license = license

    @property
    def default_error_code(self) -> int:
        """JSON-RPC error code used when a method raises an error."""
        return self._mp.uncaught_error_code

    @default_error_code.setter
    def default_error_code(self, default_error_code: int) -> None:
        self._mp.uncaught_error_code = default_error_code

    def process_request(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        log.debug("Processing request: %s", data)
        resp = self._mp.process(data)
        log.debug("Responding : %s", resp)
        return resp

    async def process_request_async(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        log.debug("Processing request: %s", data)
        resp = await self._mp.process_async(data)
        log.debug("Responding : %s", resp)
        return resp

    def discover(self) -> dict[str, Any]:
        """The OpenRPC discover method."""
        for name, rpc_method in self._mp.methods.items():
            if name == "rpc.discover":
                continue
            method = rpc_method.method
            method.params = method.params or self._get_params(rpc_method.fun)
            method.result = method.result or self._get_result(rpc_method.fun)
        return OpenRPCObject(
            openrpc="1.2.6",
            info=self._info,
            methods=[
                it.method
                for it in self._mp.methods.values()
                if it.method.name != "rpc.discover"
            ],
            components=self._components,
        ).dict(by_alias=True, exclude_unset=True)

    def _get_params(self, fun: Callable) -> list[ContentDescriptorObject]:
        # noinspection PyUnresolvedReferences,PyProtectedMember
        has_default = {
            k
            for k, v in inspect.signature(fun).parameters.items()
            if v.default != inspect._empty
        }
        return [
            ContentDescriptorObject(
                name=name,
                schema=self._get_schema(annotation),
                required=name not in has_default and self._is_required(annotation),
            )
            for name, annotation in get_type_hints(fun).items()
            if name != "return"
        ]

    def _get_result(self, fun: Callable) -> ContentDescriptorObject:
        return ContentDescriptorObject(
            name="result",
            schema=self._get_schema(get_type_hints(fun)["return"]),
            required=self._is_required(get_type_hints(fun)["return"]),
        )

    def _get_schema(self, annotation: Type) -> SchemaObject:
        if annotation == Any:
            return SchemaObject()
        if get_origin(annotation) == Union:
            return SchemaObject(
                anyOf=[self._get_schema(a) for a in get_args(annotation)]
            )

        schema_type = self._py_to_schema_type(annotation)

        if schema_type == "object":
            try:
                name = annotation.__name__
            except AttributeError:
                name = None
            if "schema" in dir(annotation):
                # noinspection PyUnresolvedReferences
                schema = SchemaObject(**annotation.schema())
                schema.title = schema.title or name
                for k, v in (schema.definitions or {}).items():
                    if k not in self._components.schemas:
                        self._components.schemas[k] = v
                # pydantic creates definitions, move them to components.
                for prop in schema.properties.values():
                    if prop.ref:
                        prop.ref = re.sub(
                            r"^#/definitions", "#/components/schemas", prop.ref
                        )
                del schema.definitions
            elif get_origin(annotation) == dict:
                schema = SchemaObject()
                schema.type = schema_type
                schema.additional_properties = True
                return schema
            else:
                schema = SchemaObject()
                schema.type = schema_type
                schema.properties = {
                    k: self._get_schema(v)
                    for k, v in get_type_hints(annotation).items()
                    if k != "return"
                }
            if schema not in self._components.schemas.values():
                self._components.schemas[name] = schema
            return SchemaObject(**{"$ref": f"#/components/schemas/{name}"})

        if schema_type == "array":
            schema = SchemaObject()
            schema.type = schema_type
            if args := get_args(annotation):
                schema.items = SchemaObject(**self._get_properties(args[0]))
            return schema

        schema = SchemaObject()
        schema.type = schema_type
        return schema

    def _py_to_schema_type(self, annotation: Any) -> Union[str, list[str]]:
        py_to_schema = {
            None: "null",
            str: "string",
            int: "number",
            float: "number",
            bool: "boolean",
        }
        origin = get_origin(annotation)
        flat_collections = [list, set, tuple]
        if origin in flat_collections or annotation in flat_collections:
            return "array"
        if dict in [origin, annotation]:
            return "object"
        if Union in [origin, annotation]:
            return self._py_to_schema_type(get_args(annotation)[0])
        if args := get_args(annotation):
            return [
                self._py_to_schema_type(arg)
                if "__name__" in dir(arg) and arg.__name__ != "NoneType"
                else "null"
                for arg in args
            ]
        if type(None) is annotation:
            return "null"
        return py_to_schema.get(annotation) or "object"

    def _get_properties(self, annotation: Type) -> dict[str, Any]:
        schema = self._get_schema(annotation)
        properties = {}
        if isinstance(schema, list):
            types = [arg.ref if arg.ref else arg.type for arg in schema]
            types = list(dict.fromkeys(types))
            if len(types) > 1:
                # noinspection PyTypedDict
                properties["type"] = types
                return properties
            schema = schema[0]
        if schema.ref:
            properties["$ref"] = schema.ref
        else:
            properties["type"] = schema.type
        return properties

    @staticmethod
    def _is_required(annotation: Any) -> bool:
        def _get_name(arg: Any) -> str:
            try:
                return arg.__name__
            except AttributeError:
                return ""

        return "NoneType" not in [_get_name(a) for a in get_args(annotation)]
