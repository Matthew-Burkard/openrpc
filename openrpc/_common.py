"""Provides classes for storing RPC method data."""
__all__ = (
    "MethodMetaData",
    "RPCMethod",
    "SecurityFunction",
    "SecurityFunctionDetails",
    "resolved_annotation",
)

import dataclasses
import inspect
from typing import Any, Awaitable, Callable, ForwardRef, Optional, Type, Union

from pydantic import BaseModel

# noinspection PyProtectedMember
from pydantic.v1.typing import evaluate_forwardref

from openrpc._depends import DependsModel
from openrpc._objects import (
    ContentDescriptor,
    Error,
    ExamplePairing,
    ExternalDocumentation,
    Link,
    ParamStructure,
    Server,
    Tag,
)

SecurityFunction = Union[
    Callable[..., dict[str, list[str]]], Callable[..., Awaitable[dict[str, list[str]]]]
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


class RPCMethod(BaseModel):
    """Hold information about a decorated Python function."""

    function: Callable
    metadata: MethodMetaData
    depends: dict[str, DependsModel]
    # Schema model needed to support Undefined.
    params_schema_model: Type[BaseModel]
    params_model: Type[BaseModel]
    result_model: Type[BaseModel]
    required: list[str]


@dataclasses.dataclass
class SecurityFunctionDetails:
    """Hold information about the security function."""

    function: SecurityFunction
    depends_params: dict[str, DependsModel]
    accepts_caller_details: bool


def resolved_annotation(annotation: Any, function: Callable) -> Any:
    """Get annotation resolved."""
    if annotation == inspect.Signature.empty:
        return Any
    globalns = getattr(function, "__globals__", {})
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return type(None) if annotation is None else annotation
