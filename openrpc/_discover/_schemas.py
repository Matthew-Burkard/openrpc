"""Module for generating Open-RPC document model and enum schemas."""

import inspect
from enum import Enum
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

from openrpc import Depends, SchemaObject

Model = TypeVar("Model", bound=BaseModel)
ModelType = Type[Model]
EnumType = TypeVar("EnumType", bound=BaseModel)
TypeOfEnumType = Type[EnumType]


def get_type_to_schema_map(functions: Iterable[Callable]) -> dict[Type, SchemaObject]:
    """Get a map of class type to JSON Schema.

    :param functions: All `method` decorated functions.
    :return: A map of class type to JSON Schema.
    """
    type_to_schema_map: dict[ModelType, SchemaObject] = {}
    for function in functions:
        # Get all model schemas used in methods including child schemas.
        for model_type in _get_models_from_function(function):
            schemas, _ = _get_model_schemas(model_type, type_to_schema_map)
            type_to_schema_map = {**type_to_schema_map, **schemas}
        # Get all enum schemas used in methods.
        for enum_type in _get_enums_from_function(function):
            type_to_schema_map[enum_type] = SchemaObject(
                title=enum_type.__name__,
                enum=[it.value for it in enum_type],
                description=enum_type.__doc__ or None,
            )
    return _get_flattened_schemas(type_to_schema_map)


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


def _get_enums_from_function(function: Callable) -> list[ModelType]:
    depends_params = [
        k
        for k, v in inspect.signature(function).parameters.items()
        if v.default is Depends
    ]
    # noinspection PydanticTypeChecker
    return [
        annotation
        for name, annotation in get_type_hints(function).items()
        if name not in depends_params
        and isinstance(annotation, Type)  # type: ignore
        and issubclass(annotation, Enum)
    ]


def _get_model_schemas(
    type_: ModelType,
    type_to_schema_map: dict[ModelType, SchemaObject],
    processed_types: Optional[list[ModelType]] = None,
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
                    child_schemas, child_types = _get_model_schemas(
                        arg, type_to_schema_map, types
                    )
                    types += child_types
                    schemas = {**schemas, **child_schemas}

        # If field is a model get schemas from that model.
        elif _is_model(field.annotation) and field.annotation is not None:
            if not (
                field.annotation in type_to_schema_map
                or field.annotation in processed_types
            ):
                # Both linters get this wrong, mypy gets it right.
                # noinspection PyTypeChecker,PydanticTypeChecker
                child_schemas, child_types = _get_model_schemas(
                    field.annotation, type_to_schema_map, types
                )
                types += child_types
                schemas = {**schemas, **child_schemas}

        # If field is an enum get enum schema.
        elif issubclass(field.annotation, Enum):
            enum_schema = schemas[type_]
            if isinstance(enum_schema.defs, dict):
                for name, definition in enum_schema.defs.items():
                    if name == field.annotation.__name__ and isinstance(
                        definition, SchemaObject
                    ):
                        schemas[field.annotation] = definition
                types += field.annotation

    return schemas, types


def _is_model(type_: Any) -> bool:
    # Type checkers are wrong about use of `Type` here.
    # noinspection PydanticTypeChecker
    return isinstance(type_, Type) and issubclass(type_, BaseModel)  # type: ignore


def _get_flattened_schemas(
    type_to_schema_map: dict[Type, SchemaObject]
) -> dict[Type, SchemaObject]:
    # Pydantic uses $defs which do not work in Open-RPC playground,
    # a number of alterations to Pydantic generated schemas need to be
    # made.
    schemas = {}
    for type_, schema in type_to_schema_map.items():
        flat_schema = schema

        # Move allOf item to top-level.
        if (
            not schema.title
            and schema.defs is not None
            and isinstance(schema.all_of, list)
        ):
            all_of = schema.all_of[0]
            if isinstance(all_of, SchemaObject) and isinstance(all_of.ref, str):
                title = all_of.ref.removeprefix("#/$defs/")
                definitions = {
                    name: definition
                    for name, definition in schema.defs.items()
                    if name != title
                }
                flat_schema = [
                    definition
                    for name, definition in schema.defs.items()
                    if name == title and isinstance(definition, SchemaObject)
                ][0]
                flat_schema.defs = definitions

        # Remove now redundant definitions.
        flat_schema.defs = None

        # Add flattened schema to new map.
        schemas[type_] = flat_schema

    return schemas
