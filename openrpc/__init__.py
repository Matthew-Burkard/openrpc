"""Provides OpenRPC objects and the RPCServer class."""

__all__ = (
    "ComponentsObject",
    "ContactObject",
    "ContentDescriptorObject",
    "ErrorObject",
    "ExampleObject",
    "ExamplePairingObject",
    "ExternalDocumentationObject",
    "InfoObject",
    "LicenseObject",
    "LinkObject",
    "MethodObject",
    "OpenRPCObject",
    "ParamStructure",
    "RPCRouter",
    "RPCServer",
    "ReferenceObject",
    "SchemaObject",
    "ServerObject",
    "ServerVariableObject",
    "TagObject",
    "Depends",
)

from openrpc._depends import Depends
from openrpc._objects import (
    ComponentsObject,
    ContactObject,
    ContentDescriptorObject,
    ErrorObject,
    ExampleObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    InfoObject,
    LicenseObject,
    LinkObject,
    MethodObject,
    OpenRPCObject,
    ParamStructure,
    ReferenceObject,
    SchemaObject,
    ServerObject,
    ServerVariableObject,
    TagObject,
)
from openrpc._router import RPCRouter
from openrpc._server import RPCServer
