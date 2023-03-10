"""Provides classes for storing RPC method data."""
from typing import Callable, Optional

from pydantic import BaseModel

from openrpc._objects import (
    ContentDescriptorObject,
    ErrorObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    LinkObject,
    ParamStructure,
    ServerObject,
    TagObject,
)


class MethodMetaData(BaseModel):
    """Hold RPC method data."""

    name: str
    params: Optional[list[ContentDescriptorObject]] = None
    result: Optional[ContentDescriptorObject] = None
    tags: Optional[list[TagObject]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentationObject] = None
    deprecated: Optional[bool] = None
    servers: Optional[list[ServerObject]] = None
    errors: Optional[list[ErrorObject]] = None
    links: Optional[list[LinkObject]] = None
    param_structure: Optional[ParamStructure] = None
    examples: Optional[list[ExamplePairingObject]] = None


class RPCMethod(BaseModel):
    """Hold information about a decorated Python function."""

    function: Callable
    metadata: MethodMetaData
    depends_params: list[str]
