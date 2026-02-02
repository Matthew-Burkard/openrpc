"""Test scope requirements.."""

import pytest

from openrpc import BaseContext, Info, Scope, RPCApp, RPCPermissionError
from tests.v11 import util

rpc = RPCApp(Info(title="Test Dependency Injection", version="0.1.0"))


read_coffee = Scope(name="coffee:read")


@rpc.method(scopes=[read_coffee])
def method_with_security(arg: int) -> int:
    """Method with required scope."""
    return arg


@pytest.mark.asyncio
async def test_scopes() -> None:
    context = BaseContext(scopes=[read_coffee.name])
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result == 1
    context = BaseContext()
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result["error"]["message"] == "Permission error"


@pytest.mark.asyncio
async def test_scoped_security_pass() -> None:
    method = rpc.scoped(method_with_security, [read_coffee.name])
    result = method(1)
    assert result == 1


@pytest.mark.asyncio
async def test_scoped_security_fail() -> None:
    method = rpc.scoped(method_with_security, [])
    with pytest.raises(RPCPermissionError):
        _ = method(0)


@pytest.mark.asyncio
async def test_security_discover() -> None:
    doc = rpc.openrpc()
    method = doc.methods[0]
    scope = method.x_scopes[0]
    assert scope == read_coffee
