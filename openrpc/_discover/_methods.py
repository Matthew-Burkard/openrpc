"""Module for generating OpenRPC document methods."""
__all__ = ("get_methods",)

import inspect
from typing import (
    Any,
    Callable,
    get_args,
    get_origin,
    get_type_hints,
    Iterable,
    Optional,
    Type,
    Union,
)

import lorem_pysum
from pydantic import create_model

from openrpc import (
    ContentDescriptorObject,
    Depends,
    ExampleObject,
    ExamplePairingObject,
    MethodObject,
    SchemaObject,
)
from openrpc._rpcmethod import RPCMethod

NoneType = type(None)
# noinspection PyUnresolvedReferences,PyProtectedMember
InspectEmpty = inspect._empty


def get_methods(
    rpc_methods: Iterable[RPCMethod], type_schema_map: dict[Type, SchemaObject]
) -> list[MethodObject]:
    """Get OpenRPC method objects.

    :param rpc_methods: Decorated functions data.
    :param type_schema_map: Type to Schema map.
    :return: OpenRPC method objects.
    """
    methods = []
    for m in rpc_methods:
        if m.metadata.name == "rpc.discover":
            continue
        method = MethodObject(
            name=m.metadata.name or m.function.__name__,
            params=m.metadata.params or _get_params(m.function, type_schema_map),
            result=m.metadata.result or _get_result(m.function, type_schema_map),
            examples=m.metadata.examples or [_get_example(m.function)],
        )
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if m.metadata.tags is not None:
            method.tags = m.metadata.tags
        if m.metadata.summary is not None:
            method.summary = m.metadata.summary
        if (description := _get_description(m)) is not None:
            method.description = description
        if m.metadata.external_docs is not None:
            method.external_docs = m.metadata.external_docs
        if m.metadata.deprecated is not None:
            method.deprecated = m.metadata.deprecated
        if m.metadata.servers is not None:
            method.servers = m.metadata.servers
        if m.metadata.errors is not None:
            method.errors = m.metadata.errors
        if m.metadata.links is not None:
            method.links = m.metadata.links
        if m.metadata.param_structure is not None:
            method.param_structure = m.metadata.param_structure
        methods.append(method)
    return methods


def _get_result(
    function: Callable, type_schema_map: dict[Type, SchemaObject]
) -> ContentDescriptorObject:
    return ContentDescriptorObject(
        name="result",
        schema=_get_schema(get_type_hints(function).get("return"), type_schema_map),
        required=_is_required(get_type_hints(function).get("return")),
    )


def _get_params(
    function: Callable, type_schema_map: dict[Type, SchemaObject]
) -> list[ContentDescriptorObject]:
    signature = inspect.signature(function)
    has_default = {
        k for k, v in signature.parameters.items() if v.default != InspectEmpty
    }
    depends = [k for k, v in signature.parameters.items() if v.default is Depends]
    type_hints = get_type_hints(function)
    return [
        ContentDescriptorObject(
            name=name,
            schema=_get_schema(type_hints.get(param.name) or Any, type_schema_map),
            required=name not in has_default
            and _is_required(_annotation(param.annotation)),
        )
        for name, param in signature.parameters.items()
        if name not in depends + ["return"]
    ]


def _is_required(annotation: Any) -> bool:
    return NoneType not in get_args(annotation)


def _get_schema(
    annotation: Any, type_schema_map: dict[Type, SchemaObject]
) -> SchemaObject:
    if annotation in (InspectEmpty, Any):
        return SchemaObject()

    if schema := type_schema_map.get(annotation):
        ref_schema = SchemaObject()
        ref_schema.ref = f"#/components/schemas/{schema.title}"
        return ref_schema

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


def _get_example(function: Callable) -> ExamplePairingObject:
    signature = inspect.signature(function)
    depends = [k for k, v in signature.parameters.items() if v.default is Depends]

    # Create model with params as fields to generate example values.
    param_example_type = create_model(  # type: ignore
        "ExampleParams",
        **{
            k: (_annotation(v.annotation), ...)
            for k, v in signature.parameters.items()
            if k not in depends
        },
    )
    param_values = lorem_pysum.generate(param_example_type, use_default_values=False)
    params = [
        ExampleObject(name=name, value=getattr(param_values, name))
        for name in param_values.model_fields
    ]

    # Create model with result as fields to generate example value.
    result_example_type = create_model(
        "ExampleResult", result=(_annotation(signature.return_annotation), ...)
    )
    result_value = lorem_pysum.generate(result_example_type, use_default_values=False)
    result = ExampleObject(value=result_value.result)  # type: ignore

    return ExamplePairingObject(params=params, result=result)


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
    if dict in (origin, annotation):
        return "object"
    if NoneType is annotation:
        return "null"
    return py_to_schema.get(annotation) or "object"


def _get_description(rpc_method: RPCMethod) -> Optional[str]:
    description = rpc_method.metadata.description
    if not description:
        description = rpc_method.function.__doc__
        # If using function doc as description only take intro line.
        if description:
            description = description.split("\n")[0]
    return description


def _annotation(annotation: Any) -> Any:
    if annotation == InspectEmpty:
        return Any
    return type(None) if annotation is None else annotation
