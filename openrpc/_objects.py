"""Python class representations of OpenRPC and JSON Schema objects."""
from __future__ import annotations

__all__ = (
    "Components",
    "Contact",
    "ContentDescriptor",
    "Error",
    "Example",
    "ExamplePairing",
    "ExternalDocumentation",
    "Info",
    "License",
    "Link",
    "Method",
    "OpenRPC",
    "ParamStructure",
    "Reference",
    "Schema",
    "SchemaType",
    "Server",
    "ServerVariable",
    "Tag",
)

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

SchemaType = Union["Schema", bool]


class ParamStructure(Enum):
    """OpenRPC method param structure options."""

    BY_NAME = "by-name"
    BY_POSITION = "by-position"
    EITHER = "either"


class Info(BaseModel):
    """The object provides metadata about the API."""

    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = Field(default=None, alias="termsOfService")
    contact: Optional[Contact] = None
    license_: Optional[License] = Field(default=None, alias="license")


class Contact(BaseModel):
    """Contact information for the exposed API."""

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


class License(BaseModel):
    """License information for the exposed API."""

    name: str
    url: Optional[str] = None


class Server(BaseModel):
    """An object representing a Server."""

    name: str
    url: str
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariable]] = None


class ServerVariable(BaseModel):
    """Represents a Server Variable for server URL template substitution."""

    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


class Method(BaseModel):
    """Describes the interface for the given method name."""

    name: str
    params: list[ContentDescriptor]
    result: ContentDescriptor
    tags: Optional[list[Tag]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )
    deprecated: Optional[bool] = False
    servers: Optional[list[Server]] = None
    errors: Optional[list[Error]] = None
    links: Optional[list[Link]] = None
    param_structure: Optional[ParamStructure] = Field(
        default=None, alias="paramStructure"
    )
    examples: Optional[list[ExamplePairing]] = None


class ContentDescriptor(BaseModel):
    """Describes either parameters or result."""

    name: str
    schema_: SchemaType = Field(alias="schema")
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


class Schema(BaseModel):
    """JSON Schema object."""

    id: Optional[str] = Field(alias="$id", default=None)
    title: Optional[str] = None
    format: Optional[str] = None
    enum: Optional[list[Any]] = None
    type: Optional[Union[str, list[str]]] = None
    all_of: Optional[list[SchemaType]] = Field(alias="allOf", default=None)
    any_of: Optional[list[SchemaType]] = Field(alias="anyOf", default=None)
    one_of: Optional[list[SchemaType]] = Field(alias="oneOf", default=None)
    not_: Optional[SchemaType] = Field(alias="not", default=None)
    pattern: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    exclusive_minimum: Optional[float] = Field(alias="exclusiveMinimum", default=None)
    exclusive_maximum: Optional[float] = Field(alias="exclusiveMaximum", default=None)
    multiple_of: Optional[float] = Field(alias="multipleOf", default=None)
    min_length: Optional[int] = Field(alias="minLength", default=None)
    max_length: Optional[int] = Field(alias="maxLength", default=None)
    properties: Optional[dict[str, SchemaType]] = None
    pattern_properties: Optional[dict[str, SchemaType]] = Field(
        alias="patternProperties", default=None
    )
    additional_properties: Optional[SchemaType] = Field(
        alias="additionalProperties", default=None
    )
    property_names: Optional[SchemaType] = Field(alias="propertyNames", default=None)
    min_properties: Optional[int] = Field(alias="minProperties", default=None)
    max_properties: Optional[int] = Field(alias="maxProperties", default=None)
    required: Optional[list[str]] = None
    defs: Optional[dict[str, SchemaType]] = Field(alias="$defs", default=None)
    items: Optional[SchemaType] = None
    prefix_items: Optional[list[SchemaType]] = Field(alias="prefixItems", default=None)
    contains: Optional[SchemaType] = None
    min_contains: Optional[int] = Field(alias="minContains", default=None)
    max_contains: Optional[int] = Field(alias="maxContains", default=None)
    min_items: Optional[int] = Field(alias="minItems", default=None)
    max_items: Optional[int] = Field(alias="maxItems", default=None)
    unique_items: Optional[bool] = Field(alias="uniqueItems", default=None)
    ref: Optional[str] = Field(alias="$ref", default=None)
    description: Optional[str] = None
    deprecated: Optional[bool] = None
    default: Optional[Any] = None
    examples: Optional[list[Any]] = None
    read_only: Optional[bool] = Field(alias="readOnly", default=None)
    write_only: Optional[bool] = Field(alias="writeOnly", default=None)
    const: Optional[Any] = None
    dependent_required: Optional[dict[str, list[str]]] = Field(
        alias="dependentRequired", default=None
    )
    dependent_schemas: Optional[dict[str, SchemaType]] = Field(
        alias="dependentSchemas", default=None
    )
    if_: Optional[SchemaType] = Field(alias="if", default=None)
    then: Optional[SchemaType] = None
    else_: Optional[SchemaType] = Field(alias="else", default=None)
    schema_: Optional[str] = Field(alias="$schema", default=None)


class ExamplePairing(BaseModel):
    """Consists of a set of example params and result."""

    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[list[Example]] = None
    result: Optional[Example] = None


class Example(BaseModel):
    """Example that is intended to match a given Content Descriptor Schema."""

    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Optional[Any] = None
    external_value: Optional[str] = Field(default=None, alias="externalValue")


class Link(BaseModel):
    """The Link object represents a possible design-time link for a result."""

    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Any] = None
    server: Optional[Server] = None


class Error(BaseModel):
    """Defines an application level error."""

    code: int
    message: str
    data: Optional[Any] = None


class Components(BaseModel):
    """Holds a set of reusable objects for different aspects of the OpenRPC."""

    content_descriptors: Optional[dict[str, ContentDescriptor]] = Field(
        default=None, alias="contentDescriptors"
    )
    schemas: Optional[dict[str, SchemaType]] = None
    examples: Optional[dict[str, Example]] = None
    links: Optional[dict[str, Link]] = None
    errors: Optional[dict[str, Error]] = None
    example_pairing_objects: Optional[dict[str, ExamplePairing]] = Field(
        default=None, alias="examplePairingObjects"
    )
    tags: Optional[dict[str, Tag]] = None


class Tag(BaseModel):
    """Adds metadata to a single tag that is used by the Method Object."""

    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )


class ExternalDocumentation(BaseModel):
    """Allows referencing an external resource for extended documentation."""

    url: str
    description: Optional[str] = None


class Reference(BaseModel):
    """A simple object to allow referencing other components in the specification."""

    ref: str = Field(alias="$ref")


class OpenRPC(BaseModel):
    """Root object of the OpenRPC document."""

    openrpc: str
    info: Info
    methods: list[Method]
    servers: Union[list[Server], Server] = Server(name="default", url="localhost")
    components: Optional[Components] = None
    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )


Info.model_rebuild()
Contact.model_rebuild()
License.model_rebuild()
Server.model_rebuild()
ServerVariable.model_rebuild()
Method.model_rebuild()
ContentDescriptor.model_rebuild()
Schema.model_rebuild()
ExamplePairing.model_rebuild()
Example.model_rebuild()
Link.model_rebuild()
Error.model_rebuild()
Components.model_rebuild()
Tag.model_rebuild()
ExternalDocumentation.model_rebuild()
OpenRPC.model_rebuild()
Reference.model_rebuild()
