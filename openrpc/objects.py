"""Python class representations of OpenRPC and JSON Schema objects."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class ParamStructure(Enum):
    """OpenRPC ParamStructure options."""

    BY_NAME = "by-name"
    BY_POSITION = "by-position"
    EITHER = "either"


class SchemaObject(BaseModel):
    """JSON Schema object."""

    id: Optional[str] = Field(alias="$id", default=None)
    title: Optional[str] = None
    format: Optional[str] = None
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
    schema_dialect: Optional[str] = Field(alias="$schema", default=None)


# noinspection PyMissingOrEmptyDocstring
class ServerVariableObject(BaseModel):
    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


# noinspection PyMissingOrEmptyDocstring
class ServerObject(BaseModel):
    name: str
    url: str
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariableObject]] = None


# noinspection PyMissingOrEmptyDocstring
class ContactObject(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


# noinspection PyMissingOrEmptyDocstring
class LicenseObject(BaseModel):
    name: str
    url: Optional[str] = None


# noinspection PyMissingOrEmptyDocstring
class InfoObject(BaseModel):
    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = Field(None, alias="termsOfService")
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None


# noinspection PyMissingOrEmptyDocstring
class ContentDescriptorObject(BaseModel):
    name: str
    json_schema: SchemaObject = Field(alias="schema")
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


# noinspection PyMissingOrEmptyDocstring
class ExternalDocumentationObject(BaseModel):
    url: str
    description: Optional[str] = None


# noinspection PyMissingOrEmptyDocstring
class TagObject(BaseModel):
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentationObject] = Field(
        None, alias="externalDocs"
    )


# noinspection PyMissingOrEmptyDocstring
class ErrorObject(BaseModel):
    code: int
    message: str
    data: Any = None


# noinspection PyMissingOrEmptyDocstring
class LinkObject(BaseModel):
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    server: Optional[ServerObject] = None


# noinspection PyMissingOrEmptyDocstring
class ExampleObject(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Any = None
    external_value: Optional[str] = Field(None, alias="externalValue")


# noinspection PyMissingOrEmptyDocstring
class ExamplePairingObject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[ExampleObject] = None
    result: Optional[ExampleObject] = None


# noinspection PyMissingOrEmptyDocstring
class MethodObject(BaseModel):
    name: Optional[str] = None
    params: Optional[list[ContentDescriptorObject]] = None
    result: Optional[ContentDescriptorObject] = None
    tags: Optional[list[TagObject]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentationObject] = Field(
        None, alias="externalDocs"
    )
    deprecated: Optional[bool] = None
    servers: Optional[list[ServerObject]] = None
    errors: Optional[list[ErrorObject]] = None
    links: Optional[list[LinkObject]] = None
    param_structure: Optional[ParamStructure] = Field(None, alias="paramStructure")
    examples: Optional[list[ExamplePairingObject]] = None


# noinspection PyMissingOrEmptyDocstring
class ComponentsObject(BaseModel):
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


# noinspection PyMissingOrEmptyDocstring
class OpenRPCObject(BaseModel):
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


SchemaObject.update_forward_refs()
