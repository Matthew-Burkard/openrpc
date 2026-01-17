"""Test error handling."""

import inspect
import json
from pathlib import Path
from typing import Any

import pytest
from jsonrpcobjects.errors import MethodNotFoundError

from openrpc import BaseContext, OpenRPCError, RPCApp
from tests.util import INTERNAL_ERROR
from tests.v11 import util

rpc = RPCApp()

error_message = "Custom error message"


@pytest.mark.asyncio
async def test_method_not_found() -> None:
    with pytest.raises(MethodNotFoundError):
        await rpc._call_method("")  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_method_not_found_raw() -> None:
    req_str = util.req_str("cabbage")
    result = await rpc.process(req_str, BaseContext())
    e = '{"id":0,"error":{"code":-32601,"message":"Method not found","data":"cabbage"},"jsonrpc":"2.0"}'  # noqa: E501
    assert result == e
    notify_str = util.notify_str("cabbage")
    result = await rpc.process(notify_str, BaseContext())
    assert result is None


@pytest.mark.asyncio
async def test_parse_error() -> None:
    req_str = "lettuce"
    result = await rpc.process(req_str, BaseContext())
    e = '{"id":null,"error":{"code":-32700,"message":"Parse error"},"jsonrpc":"2.0"}'
    assert result == e


@pytest.mark.asyncio
async def test_internal_error() -> None:
    app = RPCApp()

    async def raise_error() -> None:
        msg = "rice"
        raise ValueError(msg)

    _ = app.method()(raise_error)
    req_str = util.req_str(raise_error.__name__)
    result = await app.process(req_str, BaseContext())
    e = '{"id":0,"error":{"code":-32000,"message":"Server error"},"jsonrpc":"2.0"}'
    assert result == e
    notify_str = util.notify_str(raise_error.__name__)
    result = await app.process(notify_str, BaseContext())
    assert result is None


@pytest.mark.asyncio
async def test_internal_error_debug() -> None:
    app = RPCApp(debug=True)

    async def raise_error() -> None:
        msg = "rice"
        raise ValueError(msg)

    _ = app.method()(raise_error)
    req_str = util.req_str(raise_error.__name__)
    result = await app.process(req_str, BaseContext())
    assert result is not None
    parsed = json.loads(result)
    assert str(parsed["error"]["data"]).startswith("ValueError\n")
    assert str(parsed["error"]["data"]).endswith("ValueError: rice\n")
    notify_str = util.notify_str(raise_error.__name__)
    result = await app.process(notify_str, BaseContext())
    assert result is None


@pytest.mark.asyncio
async def test_top_level_error_handling() -> None:
    app = RPCApp()

    async def raise_error() -> None:
        raise ValueError()

    app.process_parsed_request = (
        raise_error  # pyright: ignore[reportAttributeAccessIssue]
    )
    req_str = util.req_str(raise_error.__name__)
    result = await app.process(req_str, BaseContext())
    e = '{"id":null,"error":{"code":-32603,"message":"Internal error"},"jsonrpc":"2.0"}'
    assert result == e


@pytest.mark.asyncio
async def test_top_level_error_handling_debug() -> None:
    app = RPCApp(debug=True)

    async def raise_error() -> None:
        raise ValueError()

    app.process_parsed_request = (
        raise_error  # pyright: ignore[reportAttributeAccessIssue]
    )
    req_str = util.req_str(raise_error.__name__)
    result = await app.process(req_str, BaseContext())
    assert result is not None
    parsed = json.loads(result)
    assert parsed["error"]["code"] == INTERNAL_ERROR


@rpc.method()
def method_with_error(*_args: Any) -> None:
    """That raises an error."""
    current_frame: Any = inspect.currentframe()  # type: ignore
    try:
        msg = f"{error_message}-{current_frame.f_lineno}"
        raise ValueError(msg)
    finally:
        del current_frame


@pytest.mark.asyncio
async def test_method_errors_debug() -> None:
    rpc.debug = True
    result = await util.get_result(rpc, method_with_error, [])
    absolute_path = Path(__file__).resolve()
    line = int(result["error"]["data"][-4:-1])
    error = (
        inspect.cleandoc(
            f"""
            ValueError
              File "{absolute_path}", line {line + 1}, in method_with_error
                raise ValueError(msg)
            ValueError: Custom error message-{line}
            """
        )
        + "\n"
    )
    assert result["error"]["data"] == error
    assert rpc.debug is True


@pytest.mark.asyncio
async def test_method_errors() -> None:
    rpc.debug = False
    result = await util.get_result(rpc, method_with_error, [])
    assert "data" not in result["error"]
    assert rpc.debug is False


class CustomError(OpenRPCError):
    def __init__(self, *args: object) -> None:
        self.message = "Spinach"
        self.code = -32002
        super().__init__(self.code, self.message, None, *args)


@rpc.method()
async def use_custom_error() -> None:
    raise CustomError()


@pytest.mark.asyncio
async def test_custom_error() -> None:
    rpc.debug = False
    result = await util.get_result(rpc, use_custom_error, [])
    assert result["error"]["code"] == -32002  # noqa: PLR2004
    assert result["error"]["message"] == "Spinach"


class CustomDataError(OpenRPCError):
    def __init__(self, kale: str, *args: object) -> None:
        self.message = "Spinach"
        self.code = -32003
        self.data = kale
        super().__init__(self.code, self.message, self.data, *args)


@rpc.method()
async def use_custom_data_error() -> None:
    msg = "Kale"
    raise CustomDataError(msg)


@pytest.mark.asyncio
async def test_custom_data_error() -> None:
    rpc.debug = False
    result = await util.get_result(rpc, use_custom_data_error, [])
    assert result["error"]["code"] == -32003  # noqa: PLR2004
    assert result["error"]["message"] == "Spinach"
    assert result["error"]["data"] == "Kale"
