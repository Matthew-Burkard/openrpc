from __future__ import annotations

from enum import Enum
from typing import Union, Optional, Any

from pydantic import BaseModel, Field


class ParamStructure(Enum):
    BY_NAME = 'by-name'
    BY_POSITION = 'by-position'
    EITHER = 'either'


class SchemaObject(BaseModel):
    id: Optional[str] = Field(alias='$id')
    json_schema: Optional[str] = Field(alias='schema')
    title: Optional[str] = None
    type: Optional[str] = None
    properties: Optional[dict[str, SchemaObject]] = None
    required: Optional[list[str]] = None
    definitions: Optional[dict[str, SchemaObject]]
    items: Optional[dict[str, Any]]
    ref: Optional[str] = Field(alias='$ref')


SchemaObject.update_forward_refs()


class ServerVariableObject(BaseModel):
    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


class ServerObject(BaseModel):
    name: str
    url: str = 'localhost'
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
    json_schema: SchemaObject = Field(alias='schema')
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