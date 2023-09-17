"""Module for generating OpenRPC document model and enum schemas."""

from enum import Enum
from typing import Any, get_args, Iterable, Optional, Type, TypeVar

from pydantic import BaseModel

from openrpc import Schema
from openrpc._common import RPCMethod

Model = TypeVar("Model", bound=BaseModel)
ModelType = Type[Model]
EnumType = TypeVar("EnumType", bound=BaseModel)
TypeOfEnumType = Type[EnumType]


def get_type_to_schema_map(rpc_methods: Iterable[RPCMethod]) -> dict[Type, Schema]:
    """Get a map of class type to JSON Schema.

    :param rpc_methods: All `method` decorated functions.
    :return: A map of class type to JSON Schema.
    """
    type_to_schema_map: dict[ModelType, Schema] = {}
    for method in rpc_methods:
        # Get all model schemas used in methods including child schemas.
        for model_type in _get_models_from_method(method):
            schemas, _ = _get_model_schemas(model_type, type_to_schema_map)
            type_to_schema_map = {**type_to_schema_map, **schemas}
        # Get all enum schemas used in methods.
        for enum_type in _get_enums_from_function(method):
            type_to_schema_map[enum_type] = Schema(
                title=enum_type.__name__,
                enum=[it.value for it in enum_type],
                description=enum_type.__doc__ or None,
            )
    return _get_flattened_schemas(type_to_schema_map)


def _get_models_from_method(method: RPCMethod) -> list[ModelType]:
    models = []
    for field_info in method.params_model.model_fields.values():
        models.extend(_get_models(field_info.annotation))
    for field_info in method.result_model.model_fields.values():
        models.extend(_get_models(field_info.annotation))
    return models


def _get_models(annotation: Optional[Type]) -> list[ModelType]:
    if annotation is None:
        return []
    models = []
    if _is_model(annotation):
        models.append(annotation)
    for arg in get_args(annotation):
        models.extend(_get_models(arg))
    return models


def _get_enums_from_function(method: RPCMethod) -> list:
    enums = []
    for field_info in method.params_model.model_fields.values():
        enums.extend(_get_enums(field_info.annotation))
    for field_info in method.result_model.model_fields.values():
        enums.extend(_get_enums(field_info.annotation))
    return enums


def _get_enums(annotation: Optional[Type]) -> list:
    enums = []
    if isinstance(annotation, Type) and issubclass(annotation, Enum):  # type: ignore
        enums.append(annotation)
    return enums


def _get_model_schemas(
    type_: ModelType,
    type_to_schema_map: dict[ModelType, Schema],
    processed_types: Optional[list[ModelType]] = None,
) -> tuple[dict[ModelType, Schema], list[ModelType]]:
    # `processed_types` prevents recursive schema infinite loops.
    processed_types = processed_types or []
    types = [type_]
    schemas = {type_: Schema(**type_.model_json_schema())}

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
                        definition, Schema
                    ):
                        schemas[field.annotation] = definition
                types += field.annotation

    return schemas, types


def _is_model(type_: Any) -> bool:
    # Type checkers are wrong about use of `Type` here.
    # noinspection PydanticTypeChecker
    return isinstance(type_, Type) and issubclass(type_, BaseModel)  # type: ignore


def _get_flattened_schemas(
    type_to_schema_map: dict[Type, Schema]
) -> dict[Type, Schema]:
    # Pydantic uses $defs which do not work in OpenRPC playground,
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
            if isinstance(all_of, Schema) and isinstance(all_of.ref, str):
                title = all_of.ref.removeprefix("#/$defs/")
                definitions = {
                    name: definition
                    for name, definition in schema.defs.items()
                    if name != title
                }
                flat_schema = [
                    definition
                    for name, definition in schema.defs.items()
                    if name == title and isinstance(definition, Schema)
                ][0]
                flat_schema.defs = definitions

        # Remove now redundant definitions.
        del flat_schema.defs

        # Add flattened schema to new map.
        schemas[type_] = flat_schema

    return schemas
