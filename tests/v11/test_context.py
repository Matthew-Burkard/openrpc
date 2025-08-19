import pytest

from openrpc._depends import Inject
from openrpc._objects import Info
from openrpc.app import RPCApp
from openrpc.context import BaseContext
from tests.v11 import util

AUTHORIZATION = "Authorization"
rpc = RPCApp(Info(title="Test Custom Context", version="0.1.0"), debug=True)


class Context(BaseContext):
    """Context with added fields for my transport method."""

    headers: dict[str, str] = {}


def get_user(context: Context) -> str:
    return context.headers[AUTHORIZATION]


@rpc.method()
def method_with_context(context: Context) -> str:
    return context.headers[AUTHORIZATION]


@rpc.method()
def method_with_user(user: str = Inject(get_user)) -> str:
    return user


@pytest.mark.asyncio
async def test_custom_context() -> None:
    user = "spinach"
    context = Context()
    context.headers[AUTHORIZATION] = user
    result = await util.get_result(rpc, method_with_context, [], context)
    assert result == user


@pytest.mark.asyncio
async def test_custom_context_inject() -> None:
    user = "spinach"
    context = Context()
    context.headers[AUTHORIZATION] = user
    result = await util.get_result(rpc, method_with_user, [], context)
    assert result == user
