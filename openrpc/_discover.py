"""Handle the OpenRPC "rpc.discover" method."""
import inspect
from enum import Enum
from typing import Any, Callable, get_args, get_origin, get_type_hints, Union

from openrpc._util import Function
from openrpc.objects import (
    ComponentsObject,
    ContentDescriptorObject,
    InfoObject,
    MethodObject,
    OpenRPCObject,
    SchemaObject,
)


class DiscoverHandler:
    """Used to discover an OpenRPC API."""

    def __init__(self, info: InfoObject, functions: list[Function]) -> None:
        self._info = info
        self._methods: list[MethodObject] = []
        self._components: ComponentsObject = ComponentsObject(schemas={})
        self._collect_schemas(functions)
        self._consolidate_schemas()

    def execute(self) -> OpenRPCObject:
        """Get an OpenRPCObject describing this API."""
        return OpenRPCObject(
            openrpc="1.2.6",
            info=self._info,
            methods=[
                method for method in self._methods if method.name != "rpc.discover"
            ],
            components=self._components,
        )

    def _collect_schemas(self, functions: list[Function]) -> None:
        for func in functions:
            func.metadata["name"] = func.metadata.get("name") or func.function.__name__
            func.metadata["params"] = func.metadata.get("params") or self._get_params(
                func.function
            )
            func.metadata["result"] = func.metadata.get("result") or self._get_result(
                func.function
            )
            method = MethodObject(**func.metadata)
            self._methods.append(method)

    def _consolidate_schemas(self) -> None:
        for method in self._methods:
            params = []
            for param in method.params:
                param.json_schema = self._consolidate_schema(param.json_schema)
                params.append(param)
            method.params = params
            method.result.json_schema = self._consolidate_schema(
                method.result.json_schema
            )

    def _consolidate_schema(self, schema: SchemaObject) -> SchemaObject:
        if schema.title is None:
            return schema
        self._components.schemas = self._components.schemas or {}
        # If this schema exists in components, return a reference to the
        # existing one.
        if schema in self._components.schemas.values():
            for key, val in self._components.schemas.items():
                if val == schema:
                    return SchemaObject(**{"$ref": f"#/components/schemas/{key}"})
        # Add this new schema to components and return a reference.
        self._components.schemas[schema.title] = schema
        return SchemaObject(**{"$ref": f"#/components/schemas/{schema.title}"})

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

    def _get_schema(self, annotation: Any) -> SchemaObject:
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return SchemaObject(enum=[it.value for it in annotation])
        if annotation == Any:
            return SchemaObject()
        if get_origin(annotation) == Union:
            return SchemaObject(
                anyOf=[self._get_schema(a) for a in get_args(annotation)]
            )

        schema_type = self._py_to_schema_type(annotation)

        if schema_type == "object":
            name = annotation.__name__
            if hasattr(annotation, "schema"):
                schema = SchemaObject(**annotation.schema())  # type: ignore
                schema.title = schema.title or name
                return schema
            if get_origin(annotation) == dict:
                schema = SchemaObject()
                schema.type = schema_type
                schema.additional_properties = True
                return schema

            return SchemaObject(type=schema_type, additionalProperties=True)

        if schema_type == "array":
            schema = SchemaObject(type=schema_type)
            schema.type = schema_type
            if args := get_args(annotation):
                schema.items = self._get_schema(args[0])
            return schema

        schema = SchemaObject()
        schema.type = schema_type
        return schema

    @staticmethod
    def _py_to_schema_type(annotation: Any) -> str:
        py_to_schema = {
            None: "null",
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
        }
        origin = get_origin(annotation)
        flat_collections = [list, set, tuple]
        if origin in flat_collections or annotation in flat_collections:
            return "array"
        if dict in [origin, annotation]:
            return "object"
        if type(None) is annotation:
            return "null"
        return py_to_schema.get(annotation) or "object"

    @staticmethod
    def _is_required(annotation: Any) -> bool:
        def _get_name(arg: Any) -> str:
            try:
                return arg.__name__
            except AttributeError:
                return ""

        return "NoneType" not in [_get_name(a) for a in get_args(annotation)]
