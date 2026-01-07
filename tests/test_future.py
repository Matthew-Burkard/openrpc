"""Test future annotations which behave differently."""

from __future__ import annotations

import sys
from typing import Optional, Union

from openrpc import RPCServer


def test_future() -> None:
    if sys.version_info < (3, 10):
        return

    def future(  # pyright: ignore[reportUnreachable]
        union_str_int: Union[str, int],  # noqa: ARG001
        list_str: Optional[list[str]] = None,  # noqa: ARG001
    ) -> list[str]:  # type: ignore
        """Function using future union syntax."""

    rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)
    rpc.method()(future)
    doc = rpc.discover()
    method = doc["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "name": "Generated example",
            "params": [
                {"name": "union_str_int", "value": "string"},
                {"name": "list_str", "value": None},
            ],
            "result": {"name": "Generated result", "value": ["string"]},
        }
    ]
    # Params
    assert method["params"][0]["schema"] == {
        "anyOf": [{"type": "string"}, {"type": "integer"}],
        "title": "Union Str Int",
    }
    assert method["params"][1]["schema"] == {
        "anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}],
        "default": None,
        "title": "List Str",
    }
    # Result
    assert method["result"]["schema"] == {
        "title": "Result",
        "items": {"type": "string"},
        "type": "array",
    }
