"""Test scope requirements.."""

from enum import Enum

import pytest

from openrpc import BaseContext, Info, RPCApp, RPCPermissionError
from tests.v11 import util

rpc = RPCApp(Info(title="Test Dependency Injection", version="0.1.0"))


class Scope(Enum):
    """Permission scope."""

    READ_COFFEE = "read-coffee"


@rpc.method(scopes=[Scope.READ_COFFEE.value])
def method_with_security(arg: int) -> int:
    """Method with required scope."""
    return arg


@pytest.mark.asyncio
async def test_scopes() -> None:
    context = BaseContext(scopes=[Scope.READ_COFFEE.value])
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result == 1
    context = BaseContext()
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result["error"]["message"] == "Permission error"


@pytest.mark.asyncio
async def test_scoped_security_pass() -> None:
    method = rpc.scoped(method_with_security, [Scope.READ_COFFEE.value])
    result = method(1)
    assert result == 1


@pytest.mark.asyncio
async def test_scoped_security_fail() -> None:
    method = rpc.scoped(method_with_security, [])
    with pytest.raises(RPCPermissionError):
        _ = method(0)
