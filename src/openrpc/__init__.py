"""Provides OpenRPC objects and the RPCServer class."""

__all__ = (
    "APIKeyAuth",
    "AppRouter",
    "BaseContext",
    "BearerAuth",
    "Components",
    "Contact",
    "ContentDescriptor",
    "Depends",
    "Error",
    "Example",
    "ExamplePairing",
    "ExternalDocumentation",
    "Info",
    "Inject",
    "License",
    "Link",
    "Method",
    "OAuth2",
    "OAuth2Flow",
    "OAuth2FlowType",
    "OpenRPC",
    "OpenRPCError",
    "ParamStructure",
    "RPCApp",
    "RPCMethod",
    "RPCPermissionError",
    "RPCRouter",
    "RPCServer",
    "Reference",
    "Schema",
    "SchemaType",
    "Scope",
    "SecurityFunction",
    "Server",
    "ServerVariable",
    "Tag",
    "Undefined",
    "parse_request",
)

import sys
import warnings

from jsonrpcobjects.parse import parse_request
from py_undefined import Undefined

from openrpc._app import AppRouter, RPCApp
from openrpc._common import RPCMethod, SecurityFunction
from openrpc._context import BaseContext
from openrpc._depends import Depends, Inject
from openrpc._error import OpenRPCError
from openrpc._objects import (
    APIKeyAuth,
    BearerAuth,
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
    OAuth2,
    OAuth2Flow,
    OAuth2FlowType,
    OpenRPC,
    ParamStructure,
    Reference,
    RPCPermissionError,
    Schema,
    SchemaType,
    Scope,
    Server,
    ServerVariable,
    Tag,
)
from openrpc._router import RPCRouter
from openrpc._server import RPCServer

if sys.version_info.major == 3 and sys.version_info.minor == 9:  # noqa: PLR2004
    warnings.warn(
        "Python 3.9 will not be supported in future versions of `openrpc`.",
        DeprecationWarning,
        stacklevel=2,
    )
