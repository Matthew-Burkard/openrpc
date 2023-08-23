"""Module for generating OpenRPC document methods."""
__all__ = ("get_methods",)

import datetime
import inspect
from _decimal import Decimal
from typing import (
    Any,
    Callable,
    ForwardRef,
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

# noinspection PyProtectedMember
from pydantic.v1.typing import evaluate_forwardref

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
    type_hints = {
        k: _annotation(v, function) for k, v in get_type_hints(function).items()
    }
    return ContentDescriptorObject(
        name="result",
        schema=_get_schema(type_hints.get("return"), type_schema_map),
        required=NoneType not in get_args(get_type_hints(function).get("return")),
    )


def _get_params(
    function: Callable, type_schema_map: dict[Type, SchemaObject]
) -> list[ContentDescriptorObject]:
    signature = inspect.signature(function)
    has_default = {
        k
        for k, v in signature.parameters.items()
        if v.default != inspect.Signature.empty
    }
    depends = [k for k, v in signature.parameters.items() if v.default is Depends]
    type_hints = {
        k: _annotation(v, function) for k, v in get_type_hints(function).items()
    }
    return [
        ContentDescriptorObject(
            name=name,
            schema=_get_schema(type_hints.get(param.name) or Any, type_schema_map),
            required=name not in has_default,
        )
        for name, param in signature.parameters.items()
        if name not in depends + ["return"]
    ]


def _get_schema(
    annotation: Any, type_schema_map: dict[Type, SchemaObject]
) -> SchemaObject:
    schema = SchemaObject()
    schema_type = _py_to_schema_type(annotation)

    if existing_schema := type_schema_map.get(annotation):
        schema.ref = f"#/components/schemas/{existing_schema.title}"

    elif annotation in [
        Decimal,
        datetime.date,
        datetime.time,
        datetime.datetime,
        datetime.timedelta,
    ]:
        schema = _py_object_to_schema(annotation)

    elif _is_union(get_origin(annotation)):
        schema.any_of = [_get_schema(a, type_schema_map) for a in get_args(annotation)]

    elif schema_type == "object":
        schema.type = schema_type
        # Dict annotation must have exactly 0 or two args.
        if args := get_args(annotation):
            schema.additional_properties = _get_schema(args[1], type_schema_map)

    elif schema_type == "array":
        schema.type = schema_type
        origin = get_origin(annotation)
        if args := get_args(annotation):
            if origin is tuple:
                schema.prefix_items = [
                    _get_schema(arg, type_schema_map) for arg in args
                ]
            else:
                # More than one arg in set/list annotation makes no sense.
                schema.items = _get_schema(args[0], type_schema_map)
                if origin is set:
                    schema.unique_items = True

    elif schema_type is not None:
        schema.type = schema_type

    return schema


def _get_example(function: Callable) -> ExamplePairingObject:
    signature = inspect.signature(function)
    depends = [k for k, v in signature.parameters.items() if v.default is Depends]

    # Create model with params as fields to generate example values.
    param_example_type = create_model(  # type: ignore
        "ExampleParams",
        **{
            k: (_annotation(v.annotation, function), ...)
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
        "ExampleResult",
        result=(_annotation(signature.return_annotation, function), ...),
    )
    result_value = lorem_pysum.generate(result_example_type, use_default_values=False)
    result = ExampleObject(value=result_value.result)  # type: ignore

    return ExamplePairingObject(params=params, result=result)


def _py_object_to_schema(
    annotation: Union[
        Type[Decimal],
        Type[datetime.date],
        Type[datetime.time],
        Type[datetime.datetime],
        Type[datetime.timedelta],
    ]
) -> SchemaObject:
    return {
        Decimal: SchemaObject(
            anyOf=[SchemaObject(type="number"), SchemaObject(type="string")]
        ),
        datetime.date: SchemaObject(format="date", type="string"),
        datetime.time: SchemaObject(format="time", type="string"),
        datetime.datetime: SchemaObject(format="date-time", type="string"),
        datetime.timedelta: SchemaObject(format="duration", type="string"),
    }[annotation]


def _py_to_schema_type(annotation: Any) -> Optional[str]:
    py_to_schema = {
        None: "null",
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        inspect.Signature.empty: None,
        Any: None,
    }
    origin = get_origin(annotation)
    flat_collections = [list, set, tuple]
    if origin in flat_collections or annotation in flat_collections:
        return "array"
    if dict in (origin, annotation):
        return "object"
    if NoneType is annotation:
        return "null"
    return py_to_schema.get(annotation)


def _get_description(rpc_method: RPCMethod) -> Optional[str]:
    description = rpc_method.metadata.description
    if not description:
        description = rpc_method.function.__doc__
        # If using function doc as description only take intro line.
        if description:
            description = description.split("\n")[0]
    return description


def _annotation(annotation: Any, function: Callable) -> Any:
    if annotation == inspect.Signature.empty:
        return Any
    globalns = getattr(function, "__globals__", {})
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return type(None) if annotation is None else annotation


def _is_union(origin: Any) -> bool:
    try:
        # Python3.10 union types need to be checked differently.
        return origin is Union or origin.__name__ == "UnionType"
    except AttributeError:
        return False
