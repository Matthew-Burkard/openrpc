"""Test depends."""
import json

import pytest

from openrpc import Depends, RPCServer
from tests.util import get_response, get_response_async

rpc = RPCServer(title="Test Depends", version="0.1.0")


@rpc.method()
def method_with_dep(arg: int, dep: str = Depends(lambda x: x)) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@rpc.method()
async def async_method_with_dep(arg: int, dep: str = Depends(lambda x: x)) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


def test_depends() -> None:
    header = "Coffee"
    req = {"id": 1, "method": "method_with_dep", "params": [1], "jsonrpc": "2.0"}
    result = get_response(rpc, json.dumps(req), header)
    assert result["result"] == f"1-{header}"
    req = {"id": 1, "method": "method_with_dep", "params": {"arg": 1}, "jsonrpc": "2.0"}
    result = get_response(rpc, json.dumps(req), header)
    assert result["result"] == f"1-{header}"


def test_depends_no_dependency_args() -> None:
    req = {"id": 1, "method": "method_with_dep", "params": {"arg": 1}, "jsonrpc": "2.0"}
    result = get_response(rpc, json.dumps(req))
    assert result["result"] == f"1-None"


@pytest.mark.asyncio
async def test_depends_async() -> None:
    header = "Coffee"
    req = {"id": 1, "method": "async_method_with_dep", "params": [1], "jsonrpc": "2.0"}
    result = await get_response_async(rpc, json.dumps(req), header)
    assert result["result"] == f"1-{header}"
    req = {
        "id": 1,
        "method": "async_method_with_dep",
        "params": {"arg": 1},
        "jsonrpc": "2.0",
    }
    result = await get_response_async(rpc, json.dumps(req), header)
    assert result["result"] == f"1-{header}"
