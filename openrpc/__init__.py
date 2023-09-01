"""Provides OpenRPC objects and the RPCServer class."""

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
    "RPCRouter",
    "RPCServer",
    "Reference",
    "Schema",
    "SchemaType",
    "Server",
    "ServerVariable",
    "Tag",
    "Depends",
)

from openrpc._depends import Depends
from openrpc._objects import (
    Components,
    Contact,
    ContentDescriptor,
    Error,
    Example,
    ExamplePairing,
    ExternalDocumentation,
    Info,
    License,
    Link,
    Method,
    OpenRPC,
    ParamStructure,
    Reference,
    Schema,
    SchemaType,
    Server,
    ServerVariable,
    Tag,
)
from openrpc._router import RPCRouter
from openrpc._server import RPCServer
