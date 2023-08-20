"""Test future annotations which behave differently."""
from __future__ import annotations

from openrpc import RPCServer

rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


@rpc.method()
def future(list_str: list[str] | None = None) -> list[str]:
    """Function using future union syntax."""
    return list_str or []


def test_future() -> None:
    method = rpc.discover()["methods"][0]
    # Examples
    assert [
        {
            "params": [{"name": "list_str", "value": ["string"]}],
            "result": {"value": ["string"]},
        }
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "list_str",
            "required": False,
            "schema": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "null"},
                ]
            },
        }
    ] == method["params"]
    # Result
    assert {
        "name": "result",
        "required": True,
        "schema": {"items": {"type": "string"}, "type": "array"},
    } == method["result"]
