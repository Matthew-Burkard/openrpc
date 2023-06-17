"""Handle the OpenRPC "rpc.discover" method."""

__all__ = ("DiscoverHandler",)

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
    Union,
)

import caseswitcher as cs

from openrpc import Depends
from openrpc._objects import (
    ComponentsObject,
    ContentDescriptorObject,
    InfoObject,
    MethodObject,
    OpenRPCObject,
    SchemaObject,
    SchemaType,
)
from openrpc._rpcmethod import RPCMethod

NoneType = type(None)


class DiscoverHandler:
    """Used to discover an OpenRPC API."""

    def __init__(self, info: InfoObject, functions: Iterable[RPCMethod]) -> None:
        """Init a DiscoverHandler for an OpenRPC server.

        :param info: OpenRPC info object.
        :param functions: Functions to include in discover.
        """
        self._info = info
        self._methods: list[MethodObject] = []
        self._schemas: dict[str, SchemaObject] = {}
        self._flattened_schemas: dict[str, SchemaType] = {}
        self._collect_schemas(functions)
        for schema in self._schemas.values():
            self._flatten_schema(schema)

    def execute(self) -> OpenRPCObject:
        """Get an OpenRPCObject describing this API."""
        return OpenRPCObject(
            openrpc="1.2.6",
            info=self._info,
            methods=[
                method for method in self._methods if method.name != "rpc.discover"
            ],
            components=ComponentsObject(schemas=self._flattened_schemas),
        )

    def _collect_schemas(self, functions: Iterable[RPCMethod]) -> None:
        for func in functions:
            params = self._get_params(func.function)
            result = self._get_result(func.function)
            method = MethodObject(
                **{**func.metadata.dict(), **{"params": params, "result": result}}
            )
            self._methods.append(method)

    def _flatten_schema(self, schema: SchemaType) -> SchemaType:
        if isinstance(schema, bool) or schema.title is None:
            return schema
        title = schema.title
        # If this schema exists in `flattened_schemas`, return a
        # reference to the existing one.
        if schema in self._flattened_schemas.values():
            for key, val in self._flattened_schemas.items():
                if val == schema:
                    ref_existing_schema = SchemaObject()
                    ref_existing_schema.ref = f"#/components/schemas/{key}"
                    return ref_existing_schema
        # Consolidate schema definitions.
        reference_to_consolidated_schema: dict[str, SchemaType] = {}
        recurred_schema = None
        if schema.definitions:
            # Copy because we pop/re-assign within this loop.
            definitions = schema.definitions.copy()
            for key in definitions:
                ref_schema = self._flatten_schema(schema.definitions[key])
                if ref_schema != schema.definitions[key]:
                    # If this is a recursive ref, use the definition.
                    if schema.ref and schema.ref.removeprefix("#/definitions/") == key:
                        recurred_schema = schema.definitions[key]
                    else:
                        schema.definitions.pop(key)
                reference_to_consolidated_schema[f"#/definitions/{key}"] = ref_schema
        if schema.definitions == {}:
            schema.definitions = None
        # Update schema and other component references.
        _update_references(schema, reference_to_consolidated_schema)
        for component_schema in self._flattened_schemas.values():
            _update_references(component_schema, reference_to_consolidated_schema)
        # Add this new schema to components and return a reference.
        if recurred_schema is not None and not isinstance(recurred_schema, bool):
            schema = recurred_schema
        self._flattened_schemas[cs.to_pascal(title)] = schema
        ref_schema = SchemaObject()
        ref_schema.ref = f"#/components/schemas/{schema.title}"
        return ref_schema

    def _get_params(self, fun: Callable) -> list[ContentDescriptorObject]:
        # noinspection PyUnresolvedReferences,PyProtectedMember
        has_default = {
            k
            for k, v in inspect.signature(fun).parameters.items()
            if v.default != inspect._empty
        }
        depends = [
            k
            for k, v in inspect.signature(fun).parameters.items()
            if v.default is Depends
        ]
        return [
            ContentDescriptorObject(
                name=name,
                schema=self._get_schema(annotation),
                required=name not in has_default and _is_required(annotation),
            )
            for name, annotation in get_type_hints(fun).items()
            if name not in depends + ["return"]
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
                schema.title = schema.title or cs.to_pascal(annotation.__name__)
                self._schemas[schema.title] = schema
                ref_schema = SchemaObject()
                ref_schema.ref = f"#/components/schemas/{schema.title}"
                return ref_schema
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
    def _get_name(arg: Any) -> str:
        try:
            return arg.__name__
        except AttributeError:
            return ""

    return "NoneType" not in [_get_name(a) for a in get_args(annotation)]


def _update_references(
    schema: SchemaType,
    reference_to_consolidated_schema: dict[str, SchemaType],
) -> None:
    if isinstance(schema, bool):
        return None
    for ref, consolidated_schema in reference_to_consolidated_schema.items():
        if isinstance(consolidated_schema, bool):
            continue
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
        if isinstance(schema.additional_properties, SchemaObject):
            schema.additional_properties = _get_updated_schema_references(
                ref, consolidated_schema, schema.additional_properties
            )
        if schema.properties:
            for val in schema.properties.values():
                _update_references(val, reference_to_consolidated_schema)


def _update_schema_list_references(
    original_reference: str,
    reference_schema: SchemaType,
    schemas: Optional[list[SchemaType]],
) -> Optional[list[SchemaType]]:
    updated_references_schemas = []
    for schema in schemas or []:
        updated_ref = _get_updated_schema_references(
            original_reference, reference_schema, schema
        )
        if updated_ref is not None:
            updated_references_schemas.append(updated_ref)
    return updated_references_schemas or None


def _update_schema_dict_references(
    original_reference: str,
    reference_schema: SchemaType,
    schemas: Optional[dict[str, SchemaType]],
) -> Optional[dict[str, SchemaType]]:
    updated_references_schemas = {}
    if schemas is None:
        return None
    for key, schema in schemas.items():
        updated_ref = _get_updated_schema_references(
            original_reference, reference_schema, schema
        )
        if updated_ref is not None:
            updated_references_schemas[key] = updated_ref
    return updated_references_schemas or None


def _get_updated_schema_references(
    original_reference: str,
    reference_schema: SchemaType,
    schema: Optional[SchemaType],
) -> Optional[SchemaType]:
    if isinstance(schema, SchemaObject):
        return reference_schema if schema.ref == original_reference else schema
    return schema
