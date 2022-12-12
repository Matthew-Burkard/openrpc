"""Handle the OpenRPC "rpc.discover" method."""
import copy
import inspect
from enum import Enum
from typing import (
    Any,
    Callable,
    get_args,
    get_origin,
    get_type_hints,
    Iterable,
    Optional,
    TypeVar,
    Union,
)

import caseswitcher as cs

from openrpc._util import Function
from openrpc._objects import (
    ComponentsObject,
    ContentDescriptorObject,
    InfoObject,
    MethodObject,
    OpenRPCObject,
    SchemaObject,
)

__all__ = ("DiscoverHandler",)
T = TypeVar("T", bound=Optional[SchemaObject])
NoneType = type(None)


class DiscoverHandler:
    """Used to discover an OpenRPC API."""

    def __init__(self, info: InfoObject, functions: Iterable[Function]) -> None:
        """Init a DiscoverHandler for an OpenRPC server.

        :param info: OpenRPC info object.
        :param functions: Functions to include in discover.
        """
        self._info = info
        self._methods: list[MethodObject] = []
        self._components: ComponentsObject = ComponentsObject(schemas={})
        self._collect_schemas(copy.deepcopy(list(functions)))
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
            func.metadata["name"] = func.metadata.get("name")
            func.metadata["params"] = self._get_params(func.function)
            func.metadata["result"] = self._get_result(func.function)
            method = MethodObject(**func.metadata)
            self._methods.append(method)

    def _consolidate_schemas(self) -> None:
        for method in self._methods:
            params = []
            for param in method.params:
                param.schema_ = self._consolidate_schema(param.schema_)
                params.append(param)
            method.params = params
            method.result.schema_ = self._consolidate_schema(method.result.schema_)

    def _consolidate_schema(self, schema: SchemaObject) -> SchemaObject:
        if schema.title is None:
            return schema
        # If this schema exists in components, return a reference to the
        # existing one.
        self._components.schemas = self._components.schemas or {}
        if schema in self._components.schemas.values():
            for key, val in self._components.schemas.items():
                if val == schema:
                    return SchemaObject(**{"$ref": f"#/components/schemas/{key}"})
        # Consolidate schema definitions.
        reference_to_consolidated_schema = {}
        if schema.definitions:
            for key in schema.definitions.copy():
                consolidated_schema = self._consolidate_schema(schema.definitions[key])
                if consolidated_schema != schema.definitions[key]:
                    recursive_ref = False
                    # If this is a recursive schema, leave the ref as is.
                    if schema.ref:
                        recursive_ref = schema.ref.removeprefix("#/definitions/") == key
                    if not recursive_ref:
                        schema.definitions.pop(key)
                reference_to_consolidated_schema[
                    f"#/definitions/{key}"
                ] = consolidated_schema
        if schema.definitions == {}:
            schema.definitions = None
        # Update schema and other component references.
        _update_references(schema, reference_to_consolidated_schema)
        for component_schema in self._components.schemas.values():
            _update_references(component_schema, reference_to_consolidated_schema)
        # Add this new schema to components and return a reference.
        self._components.schemas[cs.to_pascal(schema.title)] = schema
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
                required=name not in has_default and _is_required(annotation),
            )
            for name, annotation in get_type_hints(fun).items()
            if name != "return"
        ]

    def _get_result(self, fun: Callable) -> ContentDescriptorObject:
        return ContentDescriptorObject(
            name="result",
            schema=self._get_schema(get_type_hints(fun)["return"]),
            required=_is_required(get_type_hints(fun)["return"]),
        )

    def _get_schema(self, annotation: Any) -> SchemaObject:
        if annotation == Any:
            return SchemaObject()
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return SchemaObject(enum=[it.value for it in annotation])
        if get_origin(annotation) == Union:
            return SchemaObject(
                anyOf=[self._get_schema(a) for a in get_args(annotation)]
            )

        schema_type = _py_to_schema_type(annotation)

        if schema_type == "object":
            if hasattr(annotation, "schema"):
                schema = SchemaObject(**annotation.schema())  # type: ignore
                schema.title = schema.title or cs.to_title(annotation.__name__)
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

        return SchemaObject(type=schema_type)


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
    if NoneType is annotation:
        return "null"
    return py_to_schema.get(annotation) or "object"


def _is_required(annotation: Any) -> bool:
    return "NoneType" not in [a.__name__ for a in get_args(annotation)]


def _update_references(
    schema: SchemaObject,
    reference_to_consolidated_schema: dict[str, SchemaObject],
) -> None:
    for ref, consolidated_schema in reference_to_consolidated_schema.items():
        # Schema lists.
        schema.all_of = _update_schema_list_references(
            ref, consolidated_schema, schema.all_of
        )
        schema.any_of = _update_schema_list_references(
            ref, consolidated_schema, schema.any_of
        )
        schema.one_of = _update_schema_list_references(
            ref, consolidated_schema, schema.one_of
        )
        schema.prefix_items = _update_schema_list_references(
            ref, consolidated_schema, schema.prefix_items
        )
        # Schema dicts.
        schema.properties = _update_schema_dict_references(
            ref, consolidated_schema, schema.properties
        )
        schema.pattern_properties = _update_schema_dict_references(
            ref, consolidated_schema, schema.pattern_properties
        )
        schema.dependent_schemas = _update_schema_dict_references(
            ref, consolidated_schema, schema.dependent_schemas
        )
        # Schemas.
        schema.not_ = _get_updated_schema_references(
            ref, consolidated_schema, schema.not_
        )
        schema.property_names = _get_updated_schema_references(
            ref, consolidated_schema, schema.property_names
        )
        schema.contains = _get_updated_schema_references(
            ref, consolidated_schema, schema.contains
        )
        schema.if_ = _get_updated_schema_references(
            ref, consolidated_schema, schema.if_
        )
        schema.then = _get_updated_schema_references(
            ref, consolidated_schema, schema.then
        )
        schema.else_ = _get_updated_schema_references(
            ref, consolidated_schema, schema.else_
        )
        if isinstance(schema.items, SchemaObject):
            schema.items = _get_updated_schema_references(
                ref, consolidated_schema, schema.items
            )
        if schema.properties:
            for val in schema.properties.values():
                _update_references(val, reference_to_consolidated_schema)
        if schema.definitions:
            for val in schema.definitions.values():
                _update_references(val, reference_to_consolidated_schema)


def _update_schema_list_references(
    original_reference: str,
    reference_schema: SchemaObject,
    schemas: Optional[list[SchemaObject]],
) -> Optional[list[SchemaObject]]:
    updated_references_schemas = []
    for schema in schemas or []:
        updated_references_schemas.append(
            _get_updated_schema_references(original_reference, reference_schema, schema)
        )
    return updated_references_schemas or None


def _update_schema_dict_references(
    original_reference: str,
    reference_schema: SchemaObject,
    schemas: Optional[dict[str, SchemaObject]],
) -> Optional[dict[str, SchemaObject]]:
    updated_references_schemas = {}
    if schemas is None:
        return None
    for key, schema in schemas.items():
        updated_references_schemas[key] = _get_updated_schema_references(
            original_reference, reference_schema, schema
        )
    return updated_references_schemas or None


def _get_updated_schema_references(
    original_reference: str,
    reference_schema: SchemaObject,
    schema: T,
) -> Union[T, SchemaObject]:
    if isinstance(schema, SchemaObject):
        return reference_schema if schema.ref == original_reference else schema
    return schema
