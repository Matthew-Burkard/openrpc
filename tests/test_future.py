"""Test future annotations which behave differently."""

from __future__ import annotations

import sys
from typing import Optional, Union

from openrpc import RPCServer


def test_future() -> None:
    if sys.version_info < (3, 10):
        return

    # noinspection PyUnusedLocal
    def future(
        union_str_int: Union[str, int],  # noqa: ARG001
        list_str: Optional[list[str]] = None,  # noqa: ARG001
    ) -> list[str]:  # type: ignore
        """Function using future union syntax."""

    rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)
    rpc.method()(future)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "union_str_int", "value": "string"},
                {"name": "list_str", "value": None},
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
        "schema": {"items": {"type": "string"}, "type": "array", "title": "Result"},
    }
