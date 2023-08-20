"""Test depends."""
import json

import pytest

from openrpc import Depends, RPCServer
from tests.util import get_response, get_response_async

rpc = RPCServer(title="Test Depends", version="0.1.0")


@rpc.method()
def method_with_dep(arg: int, dep: str = Depends) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@rpc.method()
def method_without_dep(dep: int) -> int:
    """Method without dep and param shadowing other method dep name."""
    return dep


@rpc.method()
async def async_method_with_dep(arg: int, dep: str = Depends) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


def test_depends() -> None:
    user = "Coffee"
    req = {"id": 1, "method": "method_with_dep", "params": [1], "jsonrpc": "2.0"}
    result = get_response(rpc, json.dumps(req), {"dep": user})
    assert result["result"] == f"1-{user}"
    req = {"id": 1, "method": "method_with_dep", "params": {"arg": 1}, "jsonrpc": "2.0"}
    result = get_response(rpc, json.dumps(req), {"dep": user})
    assert result["result"] == f"1-{user}"


def test_depends_missing_dependency() -> None:
    req = {
        "id": 1,
        "method": "method_with_dep",
        "params": {"arg": 1},
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(req))
    assert result["error"]["message"] == "Server error"


def test_depends_extra_dependencies() -> None:
    user = "Coffee"
    name = "Mocha"
    req = {
        "id": 1,
        "method": "method_with_dep",
        "params": {"arg": 1},
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(req), {"dep": user, "name": name})
    assert result["result"] == f"1-{user}"


def test_depends_shadow_dep_name() -> None:
    req = {
        "id": 1,
        "method": "method_without_dep",
        "params": {"dep": 1},
        "jsonrpc": "2.0",
    }
    result = get_response(rpc, json.dumps(req), {"dep": "Mocha"})
    assert result["result"] == 1


@pytest.mark.asyncio
async def test_depends_async() -> None:
    user = "Coffee"
    req = {
        "id": 1,
        "method": "async_method_with_dep",
        "params": {"arg": 1},
        "jsonrpc": "2.0",
    }
    result = await get_response_async(rpc, json.dumps(req), {"dep": user})
    assert result["result"] == f"1-{user}"
