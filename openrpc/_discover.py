"""Module for `rpc.discover` related functions."""

__all__ = ("get_openrpc_doc",)

import inspect
from typing import (
    Any,
    Callable,
    get_args,
    get_type_hints,
    Iterable,
    Optional,
    Type,
    TypeVar,
)

from pydantic import BaseModel

from _rpcmethod import RPCMethod
from openrpc import (
    ComponentsObject,
    Depends,
    InfoObject,
    MethodObject,
    OpenRPCObject,
    SchemaObject,
)

Model = TypeVar("Model", bound=BaseModel)
ModelType = Type[Model]


def get_openrpc_doc(
    info: InfoObject, rpc_methods: Iterable[RPCMethod]
) -> OpenRPCObject:
    """Get an Open RPC document describing the RPC server.

    :param info: RPC server info.
    :param rpc_methods: RPC server methods.
    :return: The Open-RPC doc for the given server.
    """
    type_schema_map = _get_type_to_schema_map(rpc_methods)
    components = ComponentsObject(
        schemas={v.title: v for v in type_schema_map.values()}  # type: ignore
    )
    return OpenRPCObject(
        openrpc="1.2.6",
        info=info,
        methods=_get_methods(rpc_methods, type_schema_map),
        components=components,
    )


def _get_type_to_schema_map(
    methods: Iterable[RPCMethod],
) -> dict[ModelType, SchemaObject]:
    type_to_schema_map: dict[ModelType, SchemaObject] = {}
    for method in methods:
        # Get all schemas used in methods including child schemas.
        for model_type in _get_models_from_function(method.function):
            schemas, _ = _get_schemas(model_type, type_to_schema_map)
            type_to_schema_map = {**type_to_schema_map, **schemas}
    return type_to_schema_map


def _get_methods(
    rpc_methods: Iterable[RPCMethod], type_schema_map: dict[Type, SchemaObject]
) -> list[MethodObject]:
    return []


def _get_models_from_function(function: Callable) -> list[ModelType]:
    depends_params = [
        k
        for k, v in inspect.signature(function).parameters.items()
        if v.default is Depends
    ]
    return [
        annotation
        for name, annotation in get_type_hints(function).items()
        if name not in depends_params and _is_model(annotation)
    ]


def _get_schemas(
    type_: ModelType,
    type_to_schema_map: dict[ModelType, SchemaObject],
    processed_types: Optional[list[Type]] = None,
) -> tuple[dict[ModelType, SchemaObject], list[ModelType]]:
    # `processed_types` prevents recursive schema infinite loops.
    processed_types = processed_types or []
    types = [type_]
    schemas = {type_: SchemaObject(**type_.model_json_schema())}

    # Get all child schemas from fields.
    for field in type_.model_fields.values():

        # If an arg may be a model get schemas from that model.
        if args := get_args(field.annotation):
            for arg in args:
                if arg in type_to_schema_map or arg in processed_types:
                    continue
                if _is_model(arg):
                    child_schemas, child_types = _get_schemas(
                        arg, type_to_schema_map, types
                    )
                    types += child_types
                    schemas = {**schemas, **child_schemas}
            continue

        # If field is a model get schemas from that model.
        if _is_model(field.annotation):
            if (
                not (
                    field.annotation in type_to_schema_map
                    or field.annotation in processed_types
                )
                and field.annotation is not None
            ):
                # Both linters get this wrong, mypy gets it right.
                # noinspection PyTypeChecker,PydanticTypeChecker
                child_schemas, child_types = _get_schemas(
                    field.annotation, type_to_schema_map, types
                )
                types += child_types
                schemas = {**schemas, **child_schemas}

    return schemas, types


def _is_model(type_: Any) -> bool:
    return isinstance(type_, type) and issubclass(type_, BaseModel)
