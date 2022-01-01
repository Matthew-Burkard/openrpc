"""Functions shared by tests."""
import json
from json import JSONDecodeError
from typing import Union

from jsonrpcobjects.errors import JSONRPCError
from jsonrpcobjects.objects import (
    ErrorObject,
    ErrorObjectData,
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
    try:
        resp = json.loads(data)
        if resp.get("error"):
            error_resp = ErrorResponseObject(**resp)
            if resp["error"].get("data"):
                error_resp.error = ErrorObjectData(**resp["error"])
            else:
                error_resp.error = ErrorObject(**resp["error"])
            return error_resp
        if "result" in resp.keys():
            return ResultResponseObject(**resp)
        raise JSONRPCError(
            ErrorObject(code=-32000, message="Unable to parse response.")
        )
    except (JSONDecodeError, TypeError, AttributeError):
        raise JSONRPCError(
            ErrorObject(code=-32000, message="Unable to parse response.")
        )
