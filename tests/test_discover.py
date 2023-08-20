"""Test the generated "rpc.discover" method."""
import json
from enum import Enum
from typing import Any, List, Optional, Union

from jsonrpcobjects.objects import Request
from pydantic import BaseModel, Field

# noinspection PyProtectedMember
from openrpc import ContactObject, Depends, LicenseObject, RPCServer
from tests.util import Vector3


class EnumAsModelField(Enum):
    """Enum only used as a field of a model."""

    A = "A"
    B = "B"


class Vector2(BaseModel):
    """x and y values."""

    x: float
    y: float
    vanilla_model: Vector3
    enum_field: EnumAsModelField


class NestedModels(BaseModel):
    """To test models with other models as fields."""

    name: str
    position: Vector3
    path: list[Vector3]
    recursion: Optional["NestedModels"]
    list_recursion: List[Optional["NestedModels"]]
    any_of: Union[Vector3, "NestedModels"]
    dict_model_values: dict[int, Vector2] = Field(default_factory=dict)


class ListResultModel(BaseModel):
    """To test models as a list result."""

    name: str


def test_open_rpc_info() -> None:
    rpc = _rpc()
    rpc.method()(increment)
    rpc.method()(get_distance)
    rpc.method()(return_none)
    rpc.method()(default_value)
    rpc.method()(take_any_get_any)
    rpc.method()(dict_and_list)
    rpc.method()(nested_model)
    rpc.method()(typed_dict_and_list)
    rpc.method()(list_model_result)
    rpc.method()(no_annotations)
    rpc.title = rpc.title or "Test OpenRPC"
    rpc.version = rpc.version or "1.0.0"
    rpc.description = rpc.description or "Testing rpc.discover"
    rpc.terms_of_service = rpc.terms_of_service or "Coffee"
    rpc.contact = rpc.contact or ContactObject(name="mocha")
    rpc.license_ = rpc.license_ or LicenseObject(name="AGPLv3")
    request = Request(id=1, method="rpc.discover")
    resp = json.loads(rpc.process_request(request.model_dump_json()))
    discover_result = resp["result"]
    assert "1.2.6" == discover_result["openrpc"]
    assert (
        {
            "title": "Test OpenRPC",
            "version": "1.0.0",
            "description": "Testing rpc.discover",
            "termsOfService": "Coffee",
            "contact": {"name": "mocha"},
            "license": {"name": "AGPLv3"},
        },
        discover_result["info"],
    )
    # Once had problem where state was wrongfully mutated causing
    # discover to only work right the first time.
    assert rpc.discover() == rpc.discover()


def test_lists() -> None:
    rpc = _rpc()
    rpc.method()(increment)
    method = rpc.discover()["methods"][0]
    assert method["name"] == "increment"
    assert method["description"] == "pass"
    # Examples
    assert [
        {"params": [{"name": "numbers", "value": [0.0]}], "result": {"value": [0]}}
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "numbers",
            "schema": {
                "type": "array",
                "items": {"anyOf": [{"type": "integer"}, {"type": "number"}]},
            },
            "required": True,
        }
    ] == method["params"]
    # Result
    assert {
        "name": "result",
        "schema": {
            "type": "array",
            "items": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
        },
        "required": True,
    } == method["result"]


def test_schema_params() -> None:
    rpc = _rpc()
    rpc.method()(get_distance)
    method = rpc.discover()["methods"][0]
    # Examples
    assert [
        {
            "params": [
                {
                    "name": "position",
                    "value": {
                        "enum_field": "A",
                        "vanilla_model": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "x": 0.0,
                        "y": 0.0,
                    },
                },
                {
                    "name": "target",
                    "value": {
                        "enum_field": "A",
                        "vanilla_model": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "x": 0.0,
                        "y": 0.0,
                    },
                },
            ],
            "result": {
                "value": {
                    "enum_field": "A",
                    "vanilla_model": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "x": 0.0,
                    "y": 0.0,
                }
            },
        }
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "position",
            "schema": {"$ref": "#/components/schemas/Vector2"},
            "required": True,
        },
        {
            "name": "target",
            "schema": {"$ref": "#/components/schemas/Vector2"},
            "required": True,
        },
    ] == method["params"]
    # Result
    assert {
        "name": "result",
        "schema": {"$ref": "#/components/schemas/Vector2"},
        "required": True,
    } == method["result"]


def test_defaults() -> None:
    rpc = _rpc()
    rpc.method()(default_value)
    method = rpc.discover()["methods"][0]
    # Examples
    assert [
        {
            "params": [
                {"name": "a", "value": 0},
                {"name": "b", "value": 0.0},
                {"name": "c", "value": "string"},
            ],
            "result": {"value": "string"},
        }
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "a",
            "schema": {"type": "integer"},
            "required": False,
        },
        {
            "name": "b",
            "schema": {"type": "number"},
            "required": False,
        },
        {
            "name": "c",
            "schema": {"type": "string"},
            "required": False,
        },
    ] == method["params"]
    # Result
    assert {"name": "result", "schema": {"type": "string"}, "required": True} == method[
        "result"
    ]


def test_return_none() -> None:
    rpc = _rpc()
    rpc.method()(return_none)
    method = rpc.discover()["methods"][0]
    # Examples
    assert [
        {
            "params": [{"name": "optional_param", "value": "string"}],
            "result": {"value": None},
        }
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "optional_param",
            "schema": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "required": False,
        }
    ] == method["params"]
    # Result
    assert {"name": "result", "schema": {"type": "null"}, "required": True} == method[
        "result"
    ]


def test_any() -> None:
    rpc = _rpc()
    rpc.method()(take_any_get_any)
    assert {
        "description": "pass",
        "examples": [
            {
                "params": [{"name": "any_param", "value": None}],
                "result": {"value": None},
            }
        ],
        "name": "take_any_get_any",
        "params": [{"name": "any_param", "required": True, "schema": {}}],
        "result": {"name": "result", "schema": {}, "required": True},
    } == rpc.discover()["methods"][0]


def test_no_annotations() -> None:
    rpc = _rpc()
    rpc.method()(no_annotations)
    method = rpc.discover()["methods"][0]
    # Examples
    assert [
        {
            "params": [
                {"name": "a", "value": None},
                {"name": "b", "value": None},
            ],
            "result": {"value": None},
        }
    ] == method["examples"]
    # Params
    assert [
        {
            "name": "a",
            "schema": {},
            "required": True,
        },
        {
            "name": "b",
            "schema": {},
            "required": True,
        },
    ] == method["params"]
    # Result
    assert {"name": "result", "required": True, "schema": {"type": "null"}} == method[
        "result"
    ]


def test_recursive_schemas() -> None:
    rpc = _rpc()
    rpc.method()(nested_model)
    doc = rpc.discover()
    assert {
        "description": "To test models with other models as fields.",
        "properties": {
            "any_of": {
                "anyOf": [
                    {"$ref": "#/components/schemas/Vector3"},
                    {"$ref": "#/components/schemas/NestedModels"},
                ],
                "title": "Any Of",
            },
            "dict_model_values": {
                "additionalProperties": {"$ref": "#/components/schemas/Vector2"},
                "title": "Dict Model Values",
                "type": "object",
            },
            "list_recursion": {
                "items": {
                    "anyOf": [
                        {"$ref": "#/components/schemas/NestedModels"},
                        {"type": "null"},
                    ]
                },
                "title": "List Recursion",
                "type": "array",
            },
            "name": {"title": "Name", "type": "string"},
            "path": {
                "items": {"$ref": "#/components/schemas/Vector3"},
                "title": "Path",
                "type": "array",
            },
            "position": {"$ref": "#/components/schemas/Vector3"},
            "recursion": {
                "anyOf": [
                    {"$ref": "#/components/schemas/NestedModels"},
                    {"type": "null"},
                ]
            },
        },
        "required": [
            "name",
            "position",
            "path",
            "recursion",
            "list_recursion",
            "any_of",
        ],
        "title": "NestedModels",
        "type": "object",
    } == doc["components"]["schemas"]["NestedModels"]

    assert {
        "type": "object",
        "title": "Vector3",
        "description": "x, y, and z values.",
        "properties": {
            "x": {"title": "X", "type": "number"},
            "y": {"title": "Y", "type": "number"},
            "z": {"title": "Z", "type": "number"},
        },
        "required": ["x", "y", "z"],
    } == doc["components"]["schemas"]["Vector3"]


def _rpc() -> RPCServer:
    return RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


# noinspection PyUnusedLocal
def increment(numbers: list[Union[int, float]]) -> list[Union[int, str]]:
    """pass"""


# noinspection PyUnusedLocal
def get_distance(position: Vector2, target: Vector2) -> Vector2:
    """pass"""


# noinspection PyUnusedLocal
def default_value(a: int = 2, b: float = 0.99792458, c: str = "c") -> str:
    """pass"""


# noinspection PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:
    """pass"""


# noinspection PyUnusedLocal
def take_any_get_any(any_param: Any, dep: str = Depends) -> Any:
    """pass"""


# noinspection PyUnusedLocal
def dict_and_list(dict_param: dict, list_param: list) -> dict[str, list]:
    """pass"""


# noinspection PyUnusedLocal
def nested_model(a: NestedModels) -> dict[str, NestedModels]:
    """pass"""


# noinspection PyUnusedLocal
def typed_dict_and_list(
    dict_param: dict[str, int], list_param: list[dict[str, int]]
) -> dict[str, list]:
    """pass"""


# noinspection PyUnusedLocal
def list_model_result() -> list[ListResultModel]:
    """pass"""


# noinspection PyUnusedLocal
def no_annotations(a, b):
    """pass"""
