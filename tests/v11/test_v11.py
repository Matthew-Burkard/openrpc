"""Test API hooks."""

from __future__ import annotations

import pytest
from jsonrpcobjects.errors import MethodNotFoundError
from jsonrpcobjects.parse import parse_request

from openrpc._app import RPCApp
from openrpc._context import Context
from openrpc._objects import RPCPermissionError
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
async def spinach(context: Context, a: int, b: int) -> int:
    await broccoli(context, a, b)
    return a + b


@rpc.method()
async def broccoli(context: Context, a: int, b: int) -> int:
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
    context = Context(request=req_str, parsed_request=parsed)
    result: int = await rpc.call_method(broccoli.__name__, params, context)
    assert result == 1
    result: int = await rpc.call_method(broccoli.__name__, {"a": 1, "b": 0}, context)
    assert result == 1


@pytest.mark.asyncio
async def test_scopes_missing() -> None:
    context = Context(scopes=[Scope.READ_SUSHI])
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
    context = Context(scopes=[Scope.READ_SUSHI, Scope.WRITE_COFFEE])
    result: int = await rpc.call_method(cucumber.__name__, [1, 0], context)
    assert result == 1


@pytest.mark.asyncio
async def test_process_params_request() -> None:
    params = [1, 0]
    req_str = util.req_str(spinach.__name__, params)
    result = await rpc.process(req_str, Context())
    assert result == '{"id":0,"result":1,"jsonrpc":"2.0"}'


@pytest.mark.asyncio
async def test_process_request() -> None:
    req_str = util.req_str(cauliflower.__name__)
    result = await rpc.process(req_str, Context())
    assert result == '{"id":0,"result":1,"jsonrpc":"2.0"}'


@pytest.mark.asyncio
async def test_process_params_notification() -> None:
    notify_str = util.notify_str(cauliflower.__name__)
    result = await rpc.process(notify_str, Context())
    assert result is None


@pytest.mark.asyncio
async def test_process_notification() -> None:
    params = [1, 0]
    notify_str = util.notify_str(spinach.__name__, params)
    result = await rpc.process(notify_str, Context())
    assert result is None


@pytest.mark.asyncio
async def test_process_batch() -> None:
    params = [0, 1]
    notify_param_str = util.notify_str(spinach.__name__, params)
    notify_str = util.notify_str(cauliflower.__name__)
    req_str = util.req_str(cauliflower.__name__)
    req_param_str = util.req_str(spinach.__name__, params)
    batch = f"[{notify_param_str},{notify_str},{req_str},{req_param_str}]"
    result = await rpc.process(batch, Context())
    assert (
        result
        == '[{"id":0,"result":1,"jsonrpc":"2.0"},{"id":0,"result":1,"jsonrpc":"2.0"}]'
    )
