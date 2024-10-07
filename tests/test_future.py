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
    doc = rpc.discover()
    method = doc["methods"][0]
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
    assert doc["components"]["schemas"]["future_params.properties.union_str_int"] == {
        "anyOf": [{"type": "string"}, {"type": "integer"}],
        "title": "Union Str Int",
    }
    assert doc["components"]["schemas"][
        "future_params.properties.list_str.any_of.0"
    ] == {"items": {"type": "string"}, "type": "array"}
    assert doc["components"]["schemas"]["future_params.properties.list_str"] == {
        "anyOf": [
            {"$ref": "#/components/schemas/future_params.properties.list_str.any_of.0"},
            {"type": "null"},
        ],
        "default": None,
        "title": "List Str",
    }

    assert method["params"] == [
        {
            "name": "union_str_int",
            "required": True,
            "schema": {
                "$ref": "#/components/schemas/future_params.properties.union_str_int"
            },
        },
        {
            "name": "list_str",
            "required": False,
            "schema": {
                "$ref": "#/components/schemas/future_params.properties.list_str"
            },
        },
    ]
    # Result
    assert doc["components"]["schemas"]["future_result.properties.result"] == {
        "items": {"type": "string"},
        "type": "array",
        "title": "Result",
    }
    assert method["result"] == {
        "name": "result",
        "schema": {"$ref": "#/components/schemas/future_result.properties.result"},
    }
