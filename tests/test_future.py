"""Test future annotations which behave differently."""
from __future__ import annotations

from openrpc import RPCServer

rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


@rpc.method()
def test_future(_list_str: list[str] | None = None) -> None:
    assert rpc.discover()["methods"][0] == {
        "examples": [{"params": [], "result": {"value": None}}],
        "name": "test_future",
        "params": [
            {
                "name": "_list_str",
                "required": False,
                "schema": {
                    "anyOf": [
                        {"items": {"type": "string"}, "type": "array"},
                        {"type": "null"},
                    ]
                },
            }
        ],
        "result": {"name": "result", "required": True, "schema": {"type": "null"}},
    }
