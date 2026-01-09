"""Test scope requirements.."""

from enum import Enum

import pytest

from openrpc import BaseContext, Info, RPCApp
from tests.v11 import util

rpc = RPCApp(Info(title="Test Dependency Injection", version="0.1.0"), debug=True)


class Scope(Enum):
    """Permission scope."""

    READ_COFFEE = "read-coffee"


@rpc.method(scopes=[Scope.READ_COFFEE.value])
def method_with_security(arg: int) -> int:
    """Method with required scope."""
    return arg


@pytest.mark.asyncio
async def test_depends() -> None:
    context = BaseContext(scopes=[Scope.READ_COFFEE.value])
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result == 1
    context = BaseContext()
    result = await util.get_result(rpc, method_with_security, [1], context)
    assert result["error"]["data"].startswith("RPCPermissionError")
