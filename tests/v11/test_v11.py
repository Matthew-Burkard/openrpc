"""Test API hooks."""

from __future__ import annotations

import pytest
from jsonrpcobjects.errors import MethodNotFoundError
from jsonrpcobjects.parse import parse_request

from openrpc import Contact, Info, License, RPCPermissionError
from openrpc.app import RPCApp
from openrpc.context import BaseContext
from tests.v11 import util

OAUTH2 = "OAUTH2"


class Scope:
    """OAUTH2 security scope."""

    READ_SUSHI = "read_sushi"
    WRITE_COFFEE = "write_coffee"


rpc = RPCApp()


@rpc.method(scopes=[Scope.READ_SUSHI, Scope.WRITE_COFFEE])
async def cucumber(a: int, b: int) -> int:
    return a + b


@rpc.method()
async def spinach(context: BaseContext, a: int, b: int) -> int:
    await broccoli(context, a, b)
    return a + b


@rpc.method()
async def broccoli(context: BaseContext, a: int, b: int) -> int:
    print(context)
    return a - b


@rpc.method()
async def kale(a: int, b: int) -> int:
    return a + b


@rpc.method()
async def cauliflower() -> int:
    return 1


@pytest.mark.asyncio
async def test_method_call() -> None:
    result: int = await rpc.call_method(kale.__name__, [1, 0])
    assert result == 1
    result: int = await rpc.call_method(kale.__name__, {"a": 1, "b": 0})
    assert result == 1


@pytest.mark.asyncio
async def test_context_injection() -> None:
    params = [1, 0]
    req_str = util.req_str(broccoli.__name__, params)
    parsed = parse_request(req_str, debug=rpc.debug)
    assert not isinstance(parsed, list)
    context = BaseContext(raw_request=req_str, parsed_request=parsed)
    result: int = await rpc.call_method(broccoli.__name__, params, context)
    assert result == 1
    result: int = await rpc.call_method(broccoli.__name__, {"a": 1, "b": 0}, context)
    assert result == 1


@pytest.mark.asyncio
async def test_scopes_missing() -> None:
    context = BaseContext(scopes=[Scope.READ_SUSHI])
    with pytest.raises(MethodNotFoundError):
        await rpc.call_method(cucumber.__name__, [1, 0], context)
    with pytest.raises(MethodNotFoundError):
        await rpc.call_method(cucumber.__name__, [1, 0])
    app = RPCApp(debug=True)
    app.method(scopes=[Scope.READ_SUSHI, Scope.WRITE_COFFEE])(cucumber)
    with pytest.raises(RPCPermissionError):
        await app.call_method(cucumber.__name__, [1, 0], context)
    with pytest.raises(RPCPermissionError):
        await app.call_method(cucumber.__name__, [1, 0])


@pytest.mark.asyncio
async def test_scopes_present() -> None:
    context = BaseContext(scopes=[Scope.READ_SUSHI, Scope.WRITE_COFFEE])
    result: int = await rpc.call_method(cucumber.__name__, [1, 0], context)
    assert result == 1


@pytest.mark.asyncio
async def test_process_params_request() -> None:
    params = [1, 0]
    req_str = util.req_str(spinach.__name__, params)
    result = await rpc.process(req_str, BaseContext())
    assert result == '{"id":"0","result":1,"jsonrpc":"2.0"}'


@pytest.mark.asyncio
async def test_process_request() -> None:
    req_str = util.req_str(cauliflower.__name__)
    result = await rpc.process(req_str, BaseContext())
    assert result == '{"id":0,"result":1,"jsonrpc":"2.0"}'


@pytest.mark.asyncio
async def test_process_params_notification() -> None:
    notify_str = util.notify_str(cauliflower.__name__)
    result = await rpc.process(notify_str, BaseContext())
    assert result is None


@pytest.mark.asyncio
async def test_process_notification() -> None:
    params = [1, 0]
    notify_str = util.notify_str(spinach.__name__, params)
    result = await rpc.process(notify_str, BaseContext())
    assert result is None


@pytest.mark.asyncio
async def test_process_batch() -> None:
    params = [0, 1]
    notify_param_str = util.notify_str(spinach.__name__, params)
    notify_str = util.notify_str(cauliflower.__name__)
    req_str = util.req_str(cauliflower.__name__, id=1)
    req_param_str = util.req_str(spinach.__name__, params, id=2)
    batch = f"[{notify_param_str},{notify_str},{req_str},{req_param_str}]"
    result = await rpc.process(batch, BaseContext())
    assert (
        result
        == '[{"id":1,"result":1,"jsonrpc":"2.0"},{"id":2,"result":1,"jsonrpc":"2.0"}]'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_discover_info() -> None:
    app = RPCApp(
        info=Info(
            title="title",
            version="version",
            description="description",
            termsOfService="terms_of_service",
            contact=Contact(),
            license=License(name="name"),
        )
    )
    result = app.discover()
    assert result["info"]["license"]["name"] == "name"


def test_remove() -> None:
    rpc = RPCApp(Info(title="Test JSON RPC", version="1.0.0"))

    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    rpc.method()(add)
    rpc.remove("add")
    assert len(rpc.methods) == 0
