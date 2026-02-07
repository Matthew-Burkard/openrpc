"""Test depends."""

from typing import Annotated, Optional

import pytest
from jsonrpcobjects.parse import ParseResult

from openrpc import BaseContext, Depends, Info, Inject, RPCApp
from tests.v11 import util

rpc = RPCApp(Info(title="Test Dependency Injection", version="0.1.0"), debug=True)


class Scope:
    """Permission scope."""

    READ_COFFEE = "read-coffee"


async def _cucumber(context: BaseContext) -> int:
    return int(Scope.READ_COFFEE in context.scopes)


class Context(BaseContext):
    def __init__(
        self,
        string: str,
        scopes: Optional[list[str]] = None,
        raw_request: Optional[str] = None,
        parsed_request: Optional[ParseResult] = None,
    ) -> None:
        self.string = string
        super().__init__(scopes, raw_request, parsed_request)


def _inject_str(context: Context) -> str:
    return context.string


InjectStr = Annotated[str, Inject(_inject_str)]


@rpc.method()
def method_with_dep(arg: int, dep: Annotated[int, Inject(_cucumber)]) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@rpc.method()
def method_with_deps(
    str_1: str,
    str_2: str,
    inject_str: InjectStr,
) -> tuple[str, str, str]:
    """Method with dependencies to test."""
    return str_1, str_2, inject_str


@rpc.method()
async def async_method_with_dep(
    arg: int,
    dep: str = Depends(_cucumber),  # pyright: ignore[reportCallInDefaultInitializer]
) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@pytest.mark.asyncio
async def test_dependency() -> None:
    context = BaseContext(scopes=[Scope.READ_COFFEE])
    result = await util.get_result(rpc, method_with_dep, [1], context)
    assert result == "1-1"
    result = await util.get_result(rpc, method_with_dep, {"arg": 1}, context)
    assert result == "1-1"


@pytest.mark.asyncio
async def test_shared_dependency() -> None:
    assert (
        rpc._rpc_methods["method_with_deps"]  # pyright: ignore[reportPrivateUsage]
        .inject[0]
        .index
        == 2  # noqa: PLR2004
    )

    @rpc.method()
    def method_with_deps_2(  # pyright: ignore[reportUnusedFunction]
        str_1: str,
        inject_str: InjectStr,
    ) -> tuple[str, str]:
        """Method with dependencies to test."""
        return str_1, inject_str

    assert (
        rpc._rpc_methods["method_with_deps"]  # pyright: ignore[reportPrivateUsage]
        .inject[0]
        .index
        == 2  # noqa: PLR2004
    )


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
