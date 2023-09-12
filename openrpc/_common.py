"""Provides classes for storing RPC method data."""
__all__ = ("MethodMetaData", "RPCMethod", "resolved_annotation")

import inspect
from typing import Any, Callable, ForwardRef, Optional, Type

from pydantic import BaseModel

# noinspection PyProtectedMember
from pydantic.v1.typing import evaluate_forwardref

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
    depends_params: list[str]
    params_model: Type[BaseModel]
    result_model: Type[BaseModel]


def resolved_annotation(annotation: Any, function: Callable) -> Any:
    """Get annotation resolved."""
    if annotation == inspect.Signature.empty:
        return Any
    globalns = getattr(function, "__globals__", {})
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return type(None) if annotation is None else annotation
