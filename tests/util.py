"""Functions shared by tests."""
import json
from typing import Union

from jsonrpcobjects.objects import (
    ErrorResponseObject,
    ResponseType,
    ResultResponseObject,
)
from pydantic import BaseModel

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
        return ErrorResponseObject(**resp)
    if "result" in resp.keys():
        return ResultResponseObject(**resp)
