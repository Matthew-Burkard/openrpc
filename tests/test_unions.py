"""Test deserializing union types."""
import json
from typing import Union

from pydantic import BaseModel, StrictInt, StrictStr

from openrpc import RPCServer
from tests.util import get_response


class CustomA(BaseModel):
    int_field: StrictInt


class CustomB(BaseModel):
    str_field: StrictStr


def func(c: Union[CustomA, CustomB]) -> bool:
    """Test function."""
    return isinstance(c, (CustomA, CustomB))


def test_union_casting() -> None:
    rpc = RPCServer(title="Test Unions", version="1.0.0", debug=True)
    rpc.method()(func)
    req1 = {
        "id": 0,
        "method": "func",
        "params": [{"int_field": 1}],
        "jsonrpc": "2.0",
    }
    req2 = {
        "id": 0,
        "method": "func",
        "params": [{"str_field": "coffee"}],
        "jsonrpc": "2.0",
    }
    req3 = {
        "id": 0,
        "method": "func",
        "params": [{"int_field": 3.14}],
        "jsonrpc": "2.0",
    }

    assert get_response(rpc, json.dumps(req1))["result"] is True
    assert get_response(rpc, json.dumps(req2))["result"] is True
    assert get_response(rpc, json.dumps(req3))["error"]["message"] == "Invalid params"
