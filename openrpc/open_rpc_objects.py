from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

from json_types import JSON


class SchemaObject:
    pass


class ParamStructure(Enum):
    BY_NAME = 'by-name'
    BY_POSITION = 'by-position'
    EITHER = 'either'


@dataclass
class ServerVariableObject:
    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


@dataclass
class ServerObject:
    name: str
    url: str = 'localhost'
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariableObject]] = None


@dataclass
class ContactObject:
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class LicenseObject:
    name: str
    url: Optional[str] = None


@dataclass
class InfoObject:
    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None


@dataclass
class ContentDescriptorObject:
    name: str
    schema: SchemaObject
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


@dataclass
class ExternalDocumentationObject:
    url: str
    description: Optional[str] = None


@dataclass
class TagObject:
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentationObject] = None


@dataclass
class ErrorObject:
    code: int
    message: str
    data: JSON = None


@dataclass
class LinkObject:
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[dict[str, JSON]] = None
    server: Optional[ServerObject] = None


@dataclass
class ExampleObject:
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: JSON = None
    externalValue: Optional[str] = None


@dataclass
class ExamplePairingObject:
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[ExampleObject] = None
    result: Optional[ExampleObject] = None


@dataclass
class MethodObject:
    name: str
    params: list[ContentDescriptorObject]
    result: ContentDescriptorObject
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


@dataclass
class ComponentsObject:
    contentDescriptors: Optional[dict[str, ContentDescriptorObject]] = None
    schemas: Optional[dict[str, SchemaObject]] = None
    examples: Optional[dict[str, ExampleObject]] = None
    links: Optional[dict[str, LinkObject]] = None
    errors: Optional[dict[str, ErrorObject]] = None
    examplePairingObjects: Optional[dict[str, ExamplePairingObject]] = None
    tags: Optional[dict[str, TagObject]] = None


@dataclass
class OpenRPCObject:
    info: InfoObject
    methods: list[MethodObject]
    servers: Optional[Union[ServerObject, list[ServerObject]]] = None
    components: Optional[ComponentsObject] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    openrpc: str = '1.2.6'
