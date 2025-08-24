"""Test depends."""

from typing import Annotated
import pytest

from openrpc import Depends
from openrpc._depends import Inject
from openrpc._objects import Info
from openrpc.app import RPCApp
from openrpc.context import BaseContext
from tests.v11 import util

rpc = RPCApp(Info(title="Test Dependency Injection", version="0.1.0"), debug=True)


class Scope:
    """Permission scope."""

    READ_COFFEE = "read-coffee"


async def _echo(context: BaseContext) -> int:
    return int(Scope.READ_COFFEE in context.scopes)


@rpc.method()
def method_with_dep(arg: int, dep: Annotated[int, Inject(_echo)]) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@rpc.method()
async def async_method_with_dep(arg: int, dep: str = Depends(_echo)) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@pytest.mark.asyncio
async def test_depends() -> None:
    context = BaseContext(scopes=[Scope.READ_COFFEE])
    result = await util.get_result(rpc, method_with_dep, [1], context)
    assert result == "1-1"
    result = await util.get_result(rpc, method_with_dep, {"arg": 1}, context)
    assert result == "1-1"


@pytest.mark.asyncio
async def test_depends_no_dependency_args() -> None:
    result = await util.get_result(rpc, method_with_dep, {"arg": 1}, BaseContext())
    assert result == "1-0"
    result = await util.get_result(rpc, method_with_dep, {"arg": 1})
    assert result["error"]["data"].startswith("ValueError")


@pytest.mark.asyncio
async def test_depends_no_params() -> None:
    @rpc.method()
    def method_no_params(depends: Annotated[bool, Inject(lambda: True)]) -> bool:  # type: ignore  # noqa: FBT001
        """Method with depends argument and no other params."""
        return depends is True

    result = await util.get_result(rpc, method_no_params, [])
    assert result is True
