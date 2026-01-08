"""Test param rules."""

import pytest

from openrpc import Info, ParamStructure, RPCApp
from tests.v11 import util

rpc = RPCApp(Info(title="Test Depends", version="0.1.0"))
rpc_catch_all = RPCApp(Info(title="Test Depends", version="0.1.0"))
error_message = "Custom error message"


@rpc.method(param_structure=ParamStructure.BY_POSITION)
def position_add(a: int, b: int) -> int:
    """Add with params by-position."""
    return a + b


@rpc.method(param_structure=ParamStructure.BY_NAME)
def name_add(a: int, b: int) -> int:
    """Add with params by-position."""
    return a + b


@pytest.mark.asyncio
async def test_by_position() -> None:
    a, b = 2, 2
    result = await util.get_result(rpc, position_add, [a, b])
    assert result == a + b
    result = await util.get_result(rpc, position_add, {"a": a, "b": b})
    assert result["error"]["data"] == "Params must be passed by position."


@pytest.mark.asyncio
async def test_by_name() -> None:
    a, b = 2, 2
    result = await util.get_result(rpc, name_add, {"a": a, "b": b})
    assert result == a + b
    result = await util.get_result(rpc, name_add, [a, b])
    assert result["error"]["data"] == "Params must be passed by name."
