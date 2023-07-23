"""Module for generating Open-RPC document methods."""

import inspect
from typing import (
    Any,
    Callable,
    get_args,
    get_origin,
    get_type_hints,
    Iterable,
    Type,
    Union,
)

from openrpc._rpcmethod import RPCMethod
from openrpc import ContentDescriptorObject, Depends, MethodObject, SchemaObject

NoneType = type(None)


def get_methods(
    rpc_methods: Iterable[RPCMethod], type_schema_map: dict[Type, SchemaObject]
) -> list[MethodObject]:
    """Get Open-RPC method objects.

    :param rpc_methods: Decorated functions data.
    :param type_schema_map: Type to Schema map.
    :return: Open-RPC method objects.
    """
    return [
        MethodObject(
            name=rpc.metadata.name or rpc.function.__name__,
            params=rpc.metadata.params or _get_params(rpc.function, type_schema_map),
            result=rpc.metadata.result or _get_result(rpc.function, type_schema_map),
            tags=rpc.metadata.tags,
            summary=rpc.metadata.summary,
            description=rpc.metadata.description,
            externalDocs=rpc.metadata.external_docs,
            deprecated=rpc.metadata.deprecated,
            servers=rpc.metadata.servers,
            errors=rpc.metadata.errors,
            links=rpc.metadata.links,
            paramStructure=rpc.metadata.param_structure,
            examples=rpc.metadata.examples,
        )
        for rpc in rpc_methods
        if rpc.metadata.name != "rpc.discover"
    ]


def _get_result(
    function: Callable, type_schema_map: dict[Type, SchemaObject]
) -> ContentDescriptorObject:
    return ContentDescriptorObject(
        name="result",
        schema=_get_schema(get_type_hints(function)["return"], type_schema_map),
        required=_is_required(get_type_hints(function)["return"]),
    )


def _get_params(
    function: Callable, type_schema_map: dict[Type, SchemaObject]
) -> list[ContentDescriptorObject]:
    # noinspection PyUnresolvedReferences,PyProtectedMember
    has_default = {
        k
        for k, v in inspect.signature(function).parameters.items()
        if v.default != inspect._empty
    }
    depends = [
        k
        for k, v in inspect.signature(function).parameters.items()
        if v.default is Depends
    ]
    return [
        ContentDescriptorObject(
            name=name,
            schema=_get_schema(annotation, type_schema_map),
            required=name not in has_default and _is_required(annotation),
        )
        for name, annotation in get_type_hints(function).items()
        if name not in depends + ["return"]
    ]


def _is_required(annotation: Any) -> bool:
    def _get_name(arg: Any) -> str:
        try:
            return arg.__name__
        except AttributeError:
            return ""

    return "NoneType" not in [_get_name(a) for a in get_args(annotation)]


def _get_schema(
    annotation: Any, type_schema_map: dict[Type, SchemaObject]
) -> SchemaObject:
    if schema := type_schema_map.get(annotation):
        ref_schema = SchemaObject()
        ref_schema.ref = f"#/components/schemas/{schema.title}"
        return ref_schema

    if annotation == Any:
        return SchemaObject()

    if get_origin(annotation) == Union:
        return SchemaObject(
            anyOf=[_get_schema(a, type_schema_map) for a in get_args(annotation)]
        )

    schema_type = _py_to_schema_type(annotation)

    if schema_type == "object":
        return SchemaObject(type=schema_type, additionalProperties=True)

    if schema_type == "array":
        schema = SchemaObject(type=schema_type)
        if args := get_args(annotation):
            schema.items = _get_schema(args[0], type_schema_map)
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
