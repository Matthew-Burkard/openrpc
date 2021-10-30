from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class ParamStructure(Enum):
    BY_NAME = "by-name"
    BY_POSITION = "by-position"
    EITHER = "either"


class SchemaObject(BaseModel):
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


class ServerVariableObject(BaseModel):
    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


class ServerObject(BaseModel):
    name: str
    url: str = "localhost"
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariableObject]] = None


class ContactObject(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


class LicenseObject(BaseModel):
    name: str
    url: Optional[str] = None


class InfoObject(BaseModel):
    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None


class ContentDescriptorObject(BaseModel):
    name: str
    json_schema: SchemaObject = Field(alias="schema")
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


class ExternalDocumentationObject(BaseModel):
    url: str
    description: Optional[str] = None


class TagObject(BaseModel):
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentationObject] = None


class ErrorObject(BaseModel):
    code: int
    message: str
    data: Any = None


class LinkObject(BaseModel):
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    server: Optional[ServerObject] = None


class ExampleObject(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Any = None
    externalValue: Optional[str] = None


class ExamplePairingObject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[ExampleObject] = None
    result: Optional[ExampleObject] = None


class MethodObject(BaseModel):
    name: Optional[str] = None
    params: Optional[list[ContentDescriptorObject]] = None
    result: Optional[ContentDescriptorObject] = None
    tags: Optional[list[TagObject]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    deprecated: Optional[bool] = None
    servers: Optional[list[ServerObject]] = None
    errors: Optional[list[ErrorObject]] = None
    links: Optional[list[LinkObject]] = None
    paramStructure: Optional[ParamStructure] = None
    examples: Optional[list[ExamplePairingObject]] = None


class ComponentsObject(BaseModel):
    contentDescriptors: Optional[dict[str, ContentDescriptorObject]] = None
    schemas: Optional[dict[str, SchemaObject]] = None
    examples: Optional[dict[str, ExampleObject]] = None
    links: Optional[dict[str, LinkObject]] = None
    errors: Optional[dict[str, ErrorObject]] = None
    examplePairingObjects: Optional[dict[str, ExamplePairingObject]] = None
    tags: Optional[dict[str, TagObject]] = None


class OpenRPCObject(BaseModel):
    openrpc: str
    info: InfoObject
    methods: list[MethodObject]
    servers: Optional[Union[ServerObject, list[ServerObject]]] = None
    components: Optional[ComponentsObject] = None
    externalDocs: Optional[ExternalDocumentationObject] = None


SchemaObject.update_forward_refs()
