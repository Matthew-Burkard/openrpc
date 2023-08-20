"""Test removing a method from a server."""
from openrpc import InfoObject, RPCServer


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_remove() -> None:
    info = InfoObject(title="Test JSON RPC", version="1.0.0")
    rpc = RPCServer(**info.model_dump())
    rpc.method()(add)
    rpc.remove("add")
    assert 0 == len(rpc.methods)
