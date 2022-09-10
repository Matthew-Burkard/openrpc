"""Python class representations of OpenRPC and JSON Schema objects."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

__all__ = (
    "ParamStructure",
    "InfoObject",
    "ContactObject",
    "LicenseObject",
    "ServerObject",
    "ServerVariableObject",
    "MethodObject",
    "ContentDescriptorObject",
    "SchemaObject",
    "ExamplePairingObject",
    "ExampleObject",
    "LinkObject",
    "ErrorObject",
    "ComponentsObject",
    "TagObject",
    "ExternalDocumentationObject",
    "ReferenceObject",
    "OpenRPCObject",
)


class ParamStructure(Enum):
    """OpenRPC method param structure options."""

    BY_NAME = "by-name"
    BY_POSITION = "by-position"
    EITHER = "either"


class InfoObject(BaseModel):
    """The object provides metadata about the API."""

    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = Field(None, alias="termsOfService")
    contact: Optional[ContactObject] = None
    license_: Optional[LicenseObject] = Field(None, alias="license")


class ContactObject(BaseModel):
    """Contact information for the exposed API."""

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


class LicenseObject(BaseModel):
    """License information for the exposed API."""

    name: str
    url: Optional[str] = None


class ServerObject(BaseModel):
    """An object representing a Server."""

    name: str
    url: str
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariableObject]] = None


class ServerVariableObject(BaseModel):
    """Represents a Server Variable for server URL template substitution."""

    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


class MethodObject(BaseModel):
    """Describes the interface for the given method name."""

    name: str
    params: list[ContentDescriptorObject]
    result: ContentDescriptorObject
    tags: Optional[list[TagObject]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentationObject] = Field(
        None, alias="externalDocs"
    )
    deprecated: Optional[bool] = False
    servers: Optional[list[ServerObject]] = None
    errors: Optional[list[ErrorObject]] = None
    links: Optional[list[LinkObject]] = None
    param_structure: Optional[ParamStructure] = Field(None, alias="paramStructure")
    examples: Optional[list[ExamplePairingObject]] = None


class ContentDescriptorObject(BaseModel):
    """Describes either parameters or result."""

    name: str
    schema_: SchemaObject = Field(alias="schema")
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


class SchemaObject(BaseModel):
    """JSON Schema object."""

    id: Optional[str] = Field(alias="$id", default=None)
    title: Optional[str] = None
    format: Optional[str] = None
    enum: Optional[list[Any]] = None
    type: Optional[Union[str, list[str]]] = None
    all_of: Optional[list[SchemaObject]] = Field(alias="allOf", default=None)
    any_of: Optional[list[SchemaObject]] = Field(alias="anyOf", default=None)
    one_of: Optional[list[SchemaObject]] = Field(alias="oneOf", default=None)
    not_: Optional[SchemaObject] = Field(alias="not", default=None)
    pattern: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    exclusive_minimum: Optional[float] = Field(alias="exclusiveMinimum", default=None)
    exclusive_maximum: Optional[float] = Field(alias="exclusiveMaximum", default=None)
    multiple_of: Optional[float] = Field(alias="multipleOf", default=None)
    min_length: Optional[int] = Field(alias="minLength", default=None)
    max_length: Optional[int] = Field(alias="maxLength", default=None)
    properties: Optional[dict[str, SchemaObject]] = None
    pattern_properties: Optional[dict[str, SchemaObject]] = Field(
        alias="patternProperties", default=None
    )
    additional_properties: Optional[Union[bool, dict[str, Any]]] = Field(
        alias="additionalProperties", default=None
    )
    property_names: Optional[SchemaObject] = Field(alias="propertyNames", default=None)
    min_properties: Optional[int] = Field(alias="minProperties", default=None)
    max_properties: Optional[int] = Field(alias="maxProperties", default=None)
    required: Optional[list[str]] = None
    definitions: Optional[dict[str, SchemaObject]] = None
    items: Optional[Union[SchemaObject, bool]] = None
    prefix_items: Optional[list[SchemaObject]] = Field(
        alias="prefixItems", default=None
    )
    contains: Optional[SchemaObject] = None
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
    dependent_schemas: Optional[dict[str, SchemaObject]] = Field(
        alias="dependentSchemas", default=None
    )
    if_: Optional[SchemaObject] = Field(alias="if", default=None)
    then: Optional[SchemaObject] = None
    else_: Optional[SchemaObject] = Field(alias="else", default=None)
    schema_: Optional[str] = Field(alias="$schema", default=None)


class ExamplePairingObject(BaseModel):
    """Consists of a set of example params and result."""

    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[ExampleObject] = None
    result: Optional[ExampleObject] = None


class ExampleObject(BaseModel):
    """Example that is intended to match a given Content Descriptor Schema."""

    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Any = None
    external_value: Optional[str] = Field(None, alias="externalValue")


class LinkObject(BaseModel):
    """The Link object represents a possible design-time link for a result."""

    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Any] = None
    server: Optional[ServerObject] = None


class ErrorObject(BaseModel):
    """Defines an application level error."""

    code: int
    message: str
    data: Any = None


class ComponentsObject(BaseModel):
    """Holds a set of reusable objects for different aspects of the OpenRPC."""

    content_descriptors: Optional[dict[str, ContentDescriptorObject]] = Field(
        None, alias="contentDescriptors"
    )
    schemas: Optional[dict[str, SchemaObject]] = None
    examples: Optional[dict[str, ExampleObject]] = None
    links: Optional[dict[str, LinkObject]] = None
    errors: Optional[dict[str, ErrorObject]] = None
    example_pairing_objects: Optional[dict[str, ExamplePairingObject]] = Field(
        None, alias="examplePairingObjects"
    )
    tags: Optional[dict[str, TagObject]] = None


class TagObject(BaseModel):
    """Adds metadata to a single tag that is used by the Method Object."""

    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentationObject] = Field(
        None, alias="externalDocs"
    )


class ExternalDocumentationObject(BaseModel):
    """Allows referencing an external resource for extended documentation."""

    url: str
    description: Optional[str] = None


class ReferenceObject(BaseModel):
    """A simple object to allow referencing other components in the specification."""

    ref: str = Field(alias="$ref")


class OpenRPCObject(BaseModel):
    """This is the root object of the OpenRPC document."""

    openrpc: str
    info: InfoObject
    methods: list[MethodObject]
    servers: Union[list[ServerObject], ServerObject] = ServerObject(
        name="default", url="localhost"
    )
    components: Optional[ComponentsObject] = None
    external_docs: Optional[ExternalDocumentationObject] = Field(
        None, alias="externalDocs"
    )


InfoObject.update_forward_refs()
ContactObject.update_forward_refs()
LicenseObject.update_forward_refs()
ServerObject.update_forward_refs()
ServerVariableObject.update_forward_refs()
MethodObject.update_forward_refs()
ContentDescriptorObject.update_forward_refs()
SchemaObject.update_forward_refs()
ExamplePairingObject.update_forward_refs()
ExampleObject.update_forward_refs()
LinkObject.update_forward_refs()
ErrorObject.update_forward_refs()
ComponentsObject.update_forward_refs()
TagObject.update_forward_refs()
ExternalDocumentationObject.update_forward_refs()
OpenRPCObject.update_forward_refs()
ReferenceObject.update_forward_refs()
