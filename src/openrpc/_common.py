"""Provides classes for storing RPC method data."""

from __future__ import annotations

__all__ = (
    "MethodMetaData",
    "RPCMethod",
    "SecurityFunction",
    "SecurityFunctionDetails",
    "resolved_annotation",
)

import dataclasses
import inspect
from collections.abc import Awaitable, Mapping
from typing import Any, Callable, ForwardRef, Optional, Union

import typing_extensions
from pydantic import BaseModel

from openrpc._depends import DependsModel, InjectModel
from openrpc._objects import (
    ContentDescriptor,
    Error,
    ExamplePairing,
    ExternalDocumentation,
    Link,
    ParamStructure,
    Schema,
    SchemaType,
    Server,
    Tag,
)

SecurityFunction = Union[
    Callable[..., Mapping[str, list[str]]],
    Callable[..., Awaitable[Mapping[str, list[str]]]],
]


class MethodMetaData(BaseModel):
    """Hold RPC method data."""

    name: str
    params: Optional[list[ContentDescriptor]] = None
    result: Optional[ContentDescriptor] = None
    tags: Optional[list[Tag]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentation] = None
    deprecated: Optional[bool] = None
    servers: Optional[list[Server]] = None
    errors: Optional[list[Error]] = None
    links: Optional[list[Link]] = None
    param_structure: Optional[ParamStructure] = None
    examples: Optional[list[ExamplePairing]] = None
    security: dict[str, list[str]]
    scopes: list[str]


class RPCMethod(BaseModel):
    """OpenRPC framework data for a registered method."""

    context_arg: Optional[tuple[str, int]] = None
    """Argument name and position in the method."""

    depends: dict[str, DependsModel]
    """Injected dependencies using v10 and below `Depends` syntax."""

    inject: list[InjectModel]
    """Injected dependencies."""

    function: Callable[..., Any]
    """Function associated with the method."""

    metadata: MethodMetaData
    """OpenRPC method data."""

    params_schema_model: type[BaseModel]
    """Model used for method schema, excludes context and dependencies."""

    params_model: type[BaseModel]
    """Model of the method parameters type."""

    required: list[str]
    """Required parameters."""

    result_model: type[BaseModel]
    """Model of the method result type."""


@dataclasses.dataclass
class SecurityFunctionDetails:
    """Hold information about the security function."""

    function: SecurityFunction
    depends_params: dict[str, DependsModel]
    accepts_caller_details: bool


def resolved_annotation(annotation: Any, function: Callable[..., Any]) -> Any:
    """Get annotation resolved."""
    if annotation == inspect.Signature.empty:
        return Any
    globalns = getattr(function, "__globals__", {})
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = typing_extensions.evaluate_forward_ref(
            annotation, locals=globalns, globals=globalns
        )
    return type(None) if annotation is None else annotation


def get_schema(value: SchemaType | None) -> Schema:
    if value is None:
        msg = "Failed to find schema."
        raise ValueError(msg)
    if isinstance(value, bool):
        msg = "Boolean schemas are not supported"
        raise TypeError(msg)
    # If allOf is the only field and has one item, swap this with it.
    only_all_of = all(
        getattr(value, name) is None
        for name in value.model_fields_set
        if name != "all_of"
    )
    if (
        value.all_of is not None
        and only_all_of
        and len(value.all_of) == 1
        and isinstance(value.all_of[0], Schema)
    ):
        return value.all_of[0]
    return value
