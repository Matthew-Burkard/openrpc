"""Test error handling."""

import pytest
from jsonrpcobjects.errors import MethodNotFoundError

from openrpc._app import RPCApp
from openrpc._context import Context
from tests.v11 import util

rpc = RPCApp()


@pytest.mark.asyncio
async def test_method_not_found() -> None:
    with pytest.raises(MethodNotFoundError):
        await rpc.call_method("")


@pytest.mark.asyncio
async def test_method_not_found_raw() -> None:
    req_str = util.req_str("cabbage")
    result = await rpc.process(req_str, Context())
    e = '{"id":0,"error":{"code":-32601,"message":"Method not found","data":"cabbage"},"jsonrpc":"2.0"}'  # noqa: E501
    assert result == e


@pytest.mark.asyncio
async def test_parse_error() -> None:
    req_str = "lettuce"
    result = await rpc.process(req_str, Context())
    e = '{"id":null,"error":{"code":-32700,"message":"Parse error"},"jsonrpc":"2.0"}'
    assert result == e


@pytest.mark.asyncio
async def test_internal_error() -> None:
    app = RPCApp()

    async def raise_error() -> None:
        msg = "rice"
        raise ValueError(msg)

    app.method()(raise_error)
    req_str = util.req_str(raise_error.__name__)
    result = await app.process(req_str, Context())
    e = '{"id":0,"error":{"code":-32000,"message":"Server error"},"jsonrpc":"2.0"}'
    assert result == e
    notify_str = util.notify_str(raise_error.__name__)
    result = await app.process(notify_str, Context())
    assert result is None
