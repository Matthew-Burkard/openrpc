"""OpenRPC method decorator tests."""
from openrpc import RPCServer
from tests.util import get_response

rpc = RPCServer(title="Test Decorators", version="1.0.0")


@rpc.method
def add(a: int, b: int) -> int:
    """Test plain decorator."""
    return a + b


@rpc.method(name="math.subtract")
def subtract(a: int, b: int) -> int:
    """Test decorator call with kwargs."""
    return a - b


def test_plain_decorator() -> None:
    req = '{"id": 1, "method": "add", "params": [1, 3], "jsonrpc": "2.0"}'
    assert get_response(rpc, req)["result"] == 4


def test_kwargs_decorator() -> None:
    req = '{"id": 1, "method": "math.subtract", "params": [1, 3], "jsonrpc": "2.0"}'
    assert get_response(rpc, req)["result"] == -2
