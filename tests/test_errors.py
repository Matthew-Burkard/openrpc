"""Test errors."""
import inspect
import json
from pathlib import Path

import pytest

from openrpc import RPCServer

rpc = RPCServer(title="Test Depends", version="0.1.0")
rpc_catch_all = RPCServer(title="Test Depends", version="0.1.0")
error_message = "Custom error message"


@rpc.method()
def method_with_error(*_args) -> None:
    """That raises an error."""
    current_frame = inspect.currentframe()
    try:
        raise ValueError(f"{error_message}-{current_frame.f_lineno}")
    finally:
        del current_frame


# noinspection PyProtectedMember
rpc_catch_all._request_processor.process = method_with_error
# noinspection PyProtectedMember
rpc_catch_all._request_processor.process_async = method_with_error


def test_method_errors_debug() -> None:
    req = {
        "id": 1,
        "method": "method_with_error",
        "jsonrpc": "2.0",
    }
    rpc.debug = True
    result = json.loads(rpc.process_request(json.dumps(req)))
    absolute_path = Path(__file__).resolve()
    line = result["error"]["data"][-3:-1]
    error = (
        inspect.cleandoc(
            f"""
        ValueError: {error_message}-{line}
          File "{absolute_path}", line {line}, in method_with_error
            raise ValueError(f"{{error_message}}-{{current_frame.f_lineno}}")
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
    result = json.loads(rpc.process_request(json.dumps(req)))
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
    result = json.loads(rpc_catch_all.process_request(json.dumps(req)))
    assert result["error"]["data"][:-3] == f"ValueError: {error_message}"


def test_catchall_error() -> None:
    req = {
        "id": 1,
        "method": "add",
        "params": [1, 1],
        "jsonrpc": "2.0",
    }
    rpc_catch_all.debug = False
    result = json.loads(rpc_catch_all.process_request(json.dumps(req)))
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
    result = json.loads(await rpc_catch_all.process_request_async(json.dumps(req)))
    assert result["error"]["data"][:-3] == f"ValueError: {error_message}"


def test_deprecation_warning(caplog: pytest.LogCaptureFixture) -> None:
    warning_msg = "RPCServer `method` decorator must be called"
    with pytest.warns(DeprecationWarning, match=warning_msg):
        rpc.method(lambda: print())