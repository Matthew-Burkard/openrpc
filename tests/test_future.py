"""Test future annotations which behave differently."""
from __future__ import annotations

import sys
from _decimal import Decimal
from typing import Union

from pydantic import BaseModel

from openrpc import RPCServer


class Model(BaseModel):
    """The model doc string."""

    int_field: int
    float_field: float
    decimal_field: Decimal
    string_field: str
    union_str_int_field: str | int
    optional_str: str | None
    recursive_field: Model | None
    recursive_field_default: Model | None = None


def create_model(
    int_field: int,
    float_field: float,
    decimal_field: Decimal,
    string_field: str,
    union_str_int_field: str | int,
    optional_str: str | None,
    recursive_field: Model | None,
    recursive_field_default: Model | None = None,
) -> Model:
    """Method that takes model attributes and returns model instance."""
    return Model(
        int_field=int_field,
        float_field=float_field,
        decimal_field=decimal_field,
        string_field=string_field,
        union_str_int_field=union_str_int_field,
        optional_str=optional_str,
        recursive_field=recursive_field,
        recursive_field_default=recursive_field_default,
    )


def future(
    union_str_int: Union[str, int], list_str: list[str] | None = None
) -> list[str]:
    """Function using future union syntax."""
    return list_str or [union_str_int if isinstance(union_str_int, str) else ""]


def test_future() -> None:
    rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)
    rpc.method()(future)
    if sys.version_info < (3, 10):
        return None
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
            "schema": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        },
        {
            "name": "list_str",
            "required": False,
            "schema": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "null"},
                ]
            },
        },
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"items": {"type": "string"}, "type": "array"},
    }


def test_future_model() -> None:
    rpc = RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)
    rpc.method()(create_model)
    if sys.version_info < (3, 10):
        return None
    method = rpc.discover()["methods"][0]
    recursive_value = {
        "decimal_field": "1.0",
        "float_field": 1.0,
        "int_field": 1,
        "optional_str": "string",
        "recursive_field": None,
        "recursive_field_default": None,
        "string_field": "string",
        "union_str_int_field": "string",
    }
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "int_field", "value": 1},
                {"name": "float_field", "value": 1.0},
                {"name": "decimal_field", "value": "1.0"},
                {"name": "string_field", "value": "string"},
                {"name": "union_str_int_field", "value": "string"},
                {"name": "optional_str", "value": "string"},
                {"name": "recursive_field", "value": recursive_value},
                {"name": "recursive_field_default", "value": recursive_value},
            ],
            "result": {"value": recursive_value},
        }
    ]
    # Params
    assert method["params"][0] == {
        "name": "int_field",
        "required": True,
        "schema": {"type": "integer"},
    }
    assert method["params"][1] == {
        "name": "float_field",
        "required": True,
        "schema": {"type": "number"},
    }
    assert method["params"][2] == {
        "name": "decimal_field",
        "required": True,
        "schema": {"anyOf": [{"type": "number"}, {"type": "string"}]},
    }
    assert method["params"][3] == {
        "name": "string_field",
        "required": True,
        "schema": {"type": "string"},
    }
    assert method["params"][4] == {
        "name": "union_str_int_field",
        "required": True,
        "schema": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
    }
    assert method["params"][5] == {
        "name": "optional_str",
        "required": True,
        "schema": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    }
    assert method["params"][6] == {
        "name": "recursive_field",
        "required": True,
        "schema": {"anyOf": [{"$ref": "#/components/schemas/Model"}, {"type": "null"}]},
    }
    assert method["params"][7] == {
        "name": "recursive_field_default",
        "required": False,
        "schema": {"anyOf": [{"$ref": "#/components/schemas/Model"}, {"type": "null"}]},
    }
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"$ref": "#/components/schemas/Model"},
    }
