"""Test future annotations which behave differently."""
from __future__ import annotations

import sys
from typing import Union

from openrpc import RPCServer


def test_future() -> None:
    if sys.version_info < (3, 10):
        return None

    def future(
        union_str_int: Union[str, int], list_str: list[str] | None = None
    ) -> list[str]:
        """Function using future union syntax."""
        return list_str or [union_str_int if isinstance(union_str_int, str) else ""]

    rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)
    rpc.method()(future)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "union_str_int", "value": "string"},
                {"name": "list_str", "value": ["string"]},
            ],
            "result": {"value": ["string"]},
        }
    ]
    # Params
    assert method["params"] == [
        {
            "name": "union_str_int",
            "required": True,
            "schema": {
                "anyOf": [{"type": "string"}, {"type": "integer"}],
                "title": "Union Str Int",
            },
        },
        {
            "name": "list_str",
            "required": False,
            "schema": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "null"},
                ],
                "default": None,
                "title": "List Str",
            },
        },
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"items": {"type": "string"}, "type": "array", "title": "Result"},
    }
