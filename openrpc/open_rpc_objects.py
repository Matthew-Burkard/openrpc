from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

from dataclasses_json import dataclass_json

from json_types import JSON


class ParamStructure(Enum):
    BY_NAME = 'by-name'
    BY_POSITION = 'by-position'
    EITHER = 'either'


# TODO Implement full JSON Schema specification.
@dataclass_json
@dataclass
class SchemaObjectProperties:
    type: str
    description: Optional[str] = None
    exclusiveMinimum: Optional[float] = None
    items: Optional[dict] = None


# TODO Implement full JSON Schema specification.
@dataclass_json
@dataclass
class SchemaObject:
    id: Optional[str] = None
    # FIXME Expires 08/01/21
    schema: str = 'https://json-schema.org/draft/2020-12/schema'
    title: Optional[str] = None
    type: Optional[str] = None
    properties: Optional[dict[str, SchemaObjectProperties]] = None
    required: Optional[list[str]] = None


@dataclass_json
@dataclass
class ServerVariableObject:
    default: str
    enum: Optional[list[str]] = None
    description: Optional[str] = None


@dataclass_json
@dataclass
class ServerObject:
    name: str
    url: str = 'localhost'
    summary: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[dict[str, ServerVariableObject]] = None


@dataclass_json
@dataclass
class ContactObject:
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass_json
@dataclass
class LicenseObject:
    name: str
    url: Optional[str] = None


@dataclass_json
@dataclass
class InfoObject:
    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None


@dataclass_json
@dataclass
class ContentDescriptorObject:
    name: str
    schema: SchemaObject
    summary: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: bool = False


@dataclass_json
@dataclass
class ExternalDocumentationObject:
    url: str
    description: Optional[str] = None


@dataclass_json
@dataclass
class TagObject:
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentationObject] = None


@dataclass_json
@dataclass
class ErrorObject:
    code: int
    message: str
    data: JSON = None


@dataclass_json
@dataclass
class LinkObject:
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None
    method: Optional[str] = None
    params: Optional[dict[str, JSON]] = None
    server: Optional[ServerObject] = None


@dataclass_json
@dataclass
class ExampleObject:
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    value: JSON = None
    externalValue: Optional[str] = None


@dataclass_json
@dataclass
class ExamplePairingObject:
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    params: Optional[ExampleObject] = None
    result: Optional[ExampleObject] = None


@dataclass_json
@dataclass
class MethodObject:
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


@dataclass_json
@dataclass
class ComponentsObject:
    contentDescriptors: Optional[dict[str, ContentDescriptorObject]] = None
    schemas: Optional[dict[str, SchemaObject]] = None
    examples: Optional[dict[str, ExampleObject]] = None
    links: Optional[dict[str, LinkObject]] = None
    errors: Optional[dict[str, ErrorObject]] = None
    examplePairingObjects: Optional[dict[str, ExamplePairingObject]] = None
    tags: Optional[dict[str, TagObject]] = None


@dataclass_json
@dataclass
class OpenRPCObject:
    info: InfoObject
    methods: list[MethodObject]
    servers: Optional[Union[ServerObject, list[ServerObject]]] = None
    components: Optional[ComponentsObject] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    openrpc: str = '1.2.6'
