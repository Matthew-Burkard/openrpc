"""Functions shared by tests."""
from __future__ import annotations

import json

from jsonrpcobjects.objects import ErrorResponse, ResponseType, ResultResponse
from pydantic import BaseModel

from openrpc import RPCServer

INTERNAL_ERROR = -32603
INVALID_PARAMS = -32602
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
PARSE_ERROR = -32700
SERVER_ERROR = -32000


class Vector3(BaseModel):
    """x, y, and z values."""

    x: float
    y: float
    z: float


def parse_response(data: bytes | str) -> ResponseType:
    """Map a JSON-RPC2 response to the appropriate object."""
    resp = json.loads(data)
    if resp.get("error"):
        return ErrorResponse(**resp)
    if "result" in resp.keys():
        return ResultResponse(**resp)


def call(rpc_server: RPCServer, method: str, params: list | dict) -> ResponseType:
    """Call an RPC method."""
    req = {
        "id": 1,
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
    }
    return parse_response(rpc_server.process_request(json.dumps(req)))
