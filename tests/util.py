"""Functions shared by tests."""
import json
from typing import Any, Optional, Union

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


def parse_response(data: Union[bytes, str]) -> ResponseType:
    """Map a JSON-RPC2 response to the appropriate object."""
    resp = json.loads(data)
    if resp.get("error"):
        return ErrorResponse(**resp)
    return ResultResponse(**resp)


def get_response(
    rpc: RPCServer, request: str, depends: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Process request asserting that there is a `str` response."""
    resp = rpc.process_request(request, depends)
    assert resp is not None
    return json.loads(resp)


async def get_response_async(
    rpc: RPCServer, request: str, depends: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Process request asserting that there is a `str` response."""
    resp = await rpc.process_request_async(request, depends)
    assert resp is not None
    return json.loads(resp)
