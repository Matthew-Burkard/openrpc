"""Unit tests for RPC method routers."""

import pytest

from openrpc import AppRouter, Info, RPCApp
from tests.v11 import util

METHOD_NOT_FOUND_CODE = -32601
rpc = RPCApp(Info(title="RouterTestServer", version="1.0.0"))
auth_router = AppRouter(prefix="auth.")


@auth_router.method()
def method_added_before_router_included() -> None:
    """Do nothing."""


rpc.include_router(auth_router)


@auth_router.method()
def login() -> str:
    """Test auth method signature."""
    return "AUTH_TOKEN_HERE"


@pytest.mark.asyncio
async def test_router_method_call() -> None:
    result = await util.get_result(rpc, method="auth.login")
    assert result == "AUTH_TOKEN_HERE"


router_with_tags_no_prefix = AppRouter(tags=["test_tag"])
rpc.include_router(router_with_tags_no_prefix)


@router_with_tags_no_prefix.method()
def return_coffee() -> str:
    """Return "Coffee"."""
    return "Coffee"


@router_with_tags_no_prefix.method(tags=["does_nothing"])
def do_nothing() -> str:  # pyright: ignore[reportReturnType]
    """Do nothing."""


@pytest.mark.asyncio
async def test_tags_no_prefix_router_method_call() -> None:
    result = await util.get_result(rpc, method="return_coffee")
    assert result == "Coffee"


def test_tags() -> None:
    tags = [m for m in rpc.methods if m.name == "do_nothing"][0].tags
    assert [t.name for t in tags or []] == ["does_nothing", "test_tag"]


@pytest.mark.asyncio
async def test_debug() -> None:
    rpc.include_router(auth_router)
    rpc.debug = True
    for router in rpc._routers:  # pyright: ignore[reportPrivateUsage]
        assert router.debug is True
    rpc.debug = False
    for router in rpc._routers:  # pyright: ignore[reportPrivateUsage]
        assert router.debug is False
