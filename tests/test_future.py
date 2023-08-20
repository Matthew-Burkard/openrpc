"""Test future annotations which behave differently."""
from __future__ import annotations

import sys

from openrpc import RPCServer

rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


@rpc.method()
def future(list_str: list[str] | None = None) -> list[str]:
    """Function using future union syntax."""
    return list_str or []


def test_future() -> None:
    if sys.version_info < (3, 10):
        return None
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [{"name": "list_str", "value": ["string"]}],
            "result": {"value": ["string"]},
        }
    ]
    # Params
    assert method["params"] == [
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
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"items": {"type": "string"}, "type": "array"},
    }
