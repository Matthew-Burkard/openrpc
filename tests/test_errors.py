"""Test errors."""

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from openrpc import RPCServer
from tests.util import get_response, get_response_async

rpc = RPCServer(title="Test Depends", version="0.1.0")
rpc_catch_all = RPCServer(title="Test Depends", version="0.1.0")
error_message = "Custom error message"


@rpc.method()
def method_with_error(*_args: Any) -> None:
    """That raises an error."""
    current_frame: Any = inspect.currentframe()  # type: ignore
    try:
        msg = f"{error_message}-{current_frame.f_lineno}"
        raise ValueError(msg)
    finally:
        del current_frame


# noinspection PyProtectedMember
rpc_catch_all._request_processor.process = method_with_error  # type: ignore
# noinspection PyProtectedMember
rpc_catch_all._request_processor.process_async = method_with_error  # type: ignore


def test_method_errors_debug() -> None:
    req = {
        "id": 1,
        "method": "method_with_error",
        "jsonrpc": "2.0",
    }
    rpc.debug = True
    result = get_response(rpc, json.dumps(req))
    absolute_path = Path(__file__).resolve()
    line = int(result["error"]["data"][-3:-1])
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


def test_method_errors() -> None:
    req = {
        "id": 1,
        "method": "method_with_error",
        "jsonrpc": "2.0",
    }
    rpc.debug = False
    result = get_response(rpc, json.dumps(req))
    assert "data" not in result["error"]
    assert rpc.debug is False


def test_catchall_error_debug() -> None:
    req = {
        "id": 1,
        "method": "add",
        "params": [1, 1],
        "jsonrpc": "2.0",
    }
    rpc_catch_all.debug = True
    result = get_response(rpc_catch_all, json.dumps(req))
    assert result["error"]["data"][:-3] == f"ValueError: {error_message}"


def test_catchall_error() -> None:
    req = {
        "id": 1,
        "method": "add",
        "params": [1, 1],
        "jsonrpc": "2.0",
    }
    rpc_catch_all.debug = False
    result = get_response(rpc_catch_all, json.dumps(req))
    assert "data" not in result["error"]


@pytest.mark.asyncio
async def test_catchall_error_debug_async() -> None:
    # noinspection PyProtectedMember
    req = {
        "id": 1,
        "method": "add",
        "params": [1, 1],
        "jsonrpc": "2.0",
    }
    rpc_catch_all.debug = True
    result = await get_response_async(rpc_catch_all, json.dumps(req))
    assert result["error"]["data"][:-3] == f"ValueError: {error_message}"
