"""Test removing a method from a server."""

from openrpc import RPCServer


def test_remove() -> None:
    rpc = RPCServer(title="Test JSON RPC", version="1.0.0")

    def add(a: int, b: int) -> int:  # type: ignore  # noqa: ARG001
        """Add two integers."""
        return a + b

    _ = rpc.method()(add)
    rpc.remove("add")
    assert len(rpc.methods) == 0
