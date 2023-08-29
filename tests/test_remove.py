"""Test removing a method from a server."""
from openrpc import RPCServer


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_remove() -> None:
    rpc = RPCServer(title="Test JSON RPC", version="1.0.0")
    rpc.method()(add)
    rpc.remove("add")
    assert len(rpc.methods) == 0
