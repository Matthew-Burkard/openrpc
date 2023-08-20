"""Test param rules."""
import json

from openrpc import ParamStructure, RPCServer
from tests.util import get_response

rpc = RPCServer(title="Test Depends", version="0.1.0")
rpc_catch_all = RPCServer(title="Test Depends", version="0.1.0")
error_message = "Custom error message"


@rpc.method(param_structure=ParamStructure.BY_POSITION)
def position_add(a: int, b: int) -> int:
    """Add with params by-position."""
    return a + b


@rpc.method(param_structure=ParamStructure.BY_NAME)
def name_add(a: int, b: int) -> int:
    """Add with params by-position."""
    return a + b


def test_by_position() -> None:
    position_req = {
        "id": 1,
        "method": "position_add",
        "params": [2, 2],
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(position_req))
    assert result["result"] == 4
    name_req = {
        "id": 1,
        "method": "position_add",
        "params": {"a": 2, "b": 2},
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(name_req))
    assert result["error"]["data"] == "Params must be passed by position."


def test_by_name() -> None:
    name_req = {
        "id": 1,
        "method": "name_add",
        "params": {"a": 2, "b": 2},
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(name_req))
    assert result["result"] == 4
    position_req = {
        "id": 1,
        "method": "name_add",
        "params": [2, 2],
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(position_req))
    assert result["error"]["data"] == "Params must be passed by name."
