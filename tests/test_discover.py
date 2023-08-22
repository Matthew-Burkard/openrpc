"""Test the generated "rpc.discover" method."""
import datetime
import json
from _decimal import Decimal
from enum import Enum
from typing import Any, List, Optional, Union

from jsonrpcobjects.objects import Request
from pydantic import BaseModel, Field

# noinspection PyProtectedMember
from openrpc import (
    ContactObject,
    Depends,
    ErrorObject,
    ExternalDocumentationObject,
    LicenseObject,
    LinkObject,
    ParamStructure,
    RPCServer,
    ServerObject,
)
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


class ComplexObjects(BaseModel):
    date_field: datetime.date
    time_field: datetime.time
    datetime_field: datetime.datetime
    timedelta_field: datetime.timedelta
    decimal_field: Decimal


def test_open_rpc_info() -> None:
    rpc = RPCServer(
        title="Test OpenRPC",
        version="1.0.0",
        debug=True,
        description="description",
        terms_of_service="terms_of_service",
        contact=ContactObject(),
        license_=LicenseObject(name="name"),
    )
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
    resp = json.loads(rpc.process_request(request.model_dump_json()))  # type: ignore
    discover_result = resp["result"]
    assert "1.2.6" == discover_result["openrpc"]
    assert discover_result["info"] == {
        "contact": {},
        "description": "description",
        "license": {"name": "name"},
        "termsOfService": "terms_of_service",
        "title": "Test OpenRPC",
        "version": "1.0.0",
    }

    # Once had problem where state was wrongfully mutated causing
    # discover to only work right the first time.
    assert rpc.discover() == rpc.discover()


def test_method_properties() -> None:
    url = "http://localhost:8000"
    rpc = _rpc()
    rpc.method(
        summary="Summary",
        external_docs=ExternalDocumentationObject(url=url),
        deprecated=True,
        servers=[ServerObject(name="Server", url=url)],
        errors=[ErrorObject(code=0, message="Error Message")],
        links=[LinkObject(name="Link")],
        param_structure=ParamStructure.BY_NAME,
    )(method_with_properties)
    method = rpc.discover()["methods"][0]
    assert method["name"] == "method_with_properties"
    assert method["description"] == "Method to test other method properties."
    assert method["summary"] == "Summary"
    assert method["externalDocs"] == {"url": url}
    assert method["deprecated"] is True
    assert method["servers"] == [{"name": "Server", "url": url}]
    assert method["errors"] == [{"code": 0, "message": "Error Message"}]
    assert method["links"] == [{"name": "Link"}]
    assert method["paramStructure"] is ParamStructure.BY_NAME


def test_lists() -> None:
    rpc = _rpc()
    rpc.method()(increment)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {"params": [{"name": "numbers", "value": [1]}], "result": {"value": [1]}}
    ]
    # Params
    assert method["params"] == [
        {
            "name": "numbers",
            "schema": {
                "type": "array",
                "items": {"anyOf": [{"type": "integer"}, {"type": "number"}]},
            },
            "required": True,
        }
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "schema": {
            "type": "array",
            "items": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
        },
        "required": True,
    }


def test_schema_params() -> None:
    rpc = _rpc()
    rpc.method()(get_distance)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {
                    "name": "position",
                    "value": {
                        "enum_field": "A",
                        "vanilla_model": {"x": 1.0, "y": 1.0, "z": 1.0},
                        "x": 1.0,
                        "y": 1.0,
                    },
                },
                {
                    "name": "target",
                    "value": {
                        "enum_field": "A",
                        "vanilla_model": {"x": 1.0, "y": 1.0, "z": 1.0},
                        "x": 1.0,
                        "y": 1.0,
                    },
                },
            ],
            "result": {
                "value": {
                    "enum_field": "A",
                    "vanilla_model": {"x": 1.0, "y": 1.0, "z": 1.0},
                    "x": 1.0,
                    "y": 1.0,
                }
            },
        }
    ]
    # Params
    assert method["params"] == [
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
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "schema": {"$ref": "#/components/schemas/Vector2"},
        "required": True,
    }


def test_defaults() -> None:
    rpc = _rpc()
    rpc.method()(default_value)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "a", "value": 1},
                {"name": "b", "value": 1.0},
                {"name": "c", "value": "string"},
            ],
            "result": {"value": "string"},
        }
    ]
    # Params
    assert method["params"] == [
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
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "schema": {"type": "string"},
        "required": True,
    }


def test_return_none() -> None:
    rpc = _rpc()
    rpc.method()(return_none)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [{"name": "optional_param", "value": "string"}],
            "result": {"value": None},
        }
    ]
    # Params
    assert method["params"] == [
        {
            "name": "optional_param",
            "schema": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "required": True,
        }
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "schema": {"type": "null"},
        "required": True,
    }


def test_any() -> None:
    rpc = _rpc()
    rpc.method()(take_any_get_any)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {"params": [{"name": "any_param", "value": {}}], "result": {"value": {}}}
    ]
    # Params
    assert method["params"] == [{"name": "any_param", "required": True, "schema": {}}]
    # Result
    assert method["result"] == {"name": "result", "schema": {}, "required": True}


def test_no_annotations() -> None:
    rpc = _rpc()
    rpc.method()(no_annotations)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "a", "value": {}},
                {"name": "b", "value": {}},
            ],
            "result": {"value": {}},
        }
    ]
    # Params
    assert method["params"] == [
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
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"type": "null"},
    }


def test_complex_objects() -> None:
    rpc = _rpc()
    rpc.method()(method_using_complex_objects)
    method = rpc.discover()["methods"][0]
    # Examples
    assert method["examples"] == [
        {
            "params": [
                {"name": "date_field", "value": "1788-06-21"},
                {"name": "time_field", "value": "00:00:00"},
                {"name": "datetime_field", "value": "1788-06-21T00:00:00"},
                {"name": "timedelta_field", "value": "PT0S"},
                {"name": "decimal_field", "value": "1.0"},
            ],
            "result": {
                "value": {
                    "date_field": "1788-06-21",
                    "datetime_field": "1788-06-21T00:00:00",
                    "decimal_field": "1.0",
                    "time_field": "00:00:00",
                    "timedelta_field": "PT0S",
                }
            },
        }
    ]
    # Params
    assert method["params"] == [
        {
            "name": "date_field",
            "required": True,
            "schema": {"format": "date", "type": "string"},
        },
        {
            "name": "time_field",
            "required": True,
            "schema": {"format": "time", "type": "string"},
        },
        {
            "name": "datetime_field",
            "required": True,
            "schema": {"format": "date-time", "type": "string"},
        },
        {
            "name": "timedelta_field",
            "required": True,
            "schema": {"format": "duration", "type": "string"},
        },
        {
            "name": "decimal_field",
            "required": True,
            "schema": {"anyOf": [{"type": "number"}, {"type": "string"}]},
        },
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"$ref": "#/components/schemas/ComplexObjects"},
    }


def test_recursive_schemas() -> None:
    rpc = _rpc()
    rpc.method()(nested_model)
    doc = rpc.discover()
    assert doc["components"]["schemas"]["NestedModels"] == {
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
    }

    assert doc["components"]["schemas"]["Vector3"] == {
        "type": "object",
        "title": "Vector3",
        "description": "x, y, and z values.",
        "properties": {
            "x": {"title": "X", "type": "number"},
            "y": {"title": "Y", "type": "number"},
            "z": {"title": "Z", "type": "number"},
        },
        "required": ["x", "y", "z"],
    }


def _rpc() -> RPCServer:
    return RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


# noinspection PyMissingOrEmptyDocstring
def increment(numbers: list[Union[int, float]]) -> list[Union[int, str]]:
    """Collections and unions."""
    return list(map(int, numbers))


def get_distance(position: Vector2, target: Vector2) -> Vector2:
    """Function with basic model annotations."""
    return position or target


def default_value(a: int = 2, b: float = 0.99792458, c: str = "c") -> str:
    """Function with default values for params."""
    return f"{a}{b}{c}"


# noinspection PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:
    """Function with optional param that always returns None."""
    return None


def take_any_get_any(any_param: Any, dep: str = Depends) -> Any:
    """Function that takes and returns any type, uses Dep argument."""
    return any_param + dep


def dict_and_list(dict_param: dict, list_param: list) -> dict[str, list]:
    """For testing dict and list type annotations."""
    dict_param[""] = list_param
    return dict_param


def typed_dict_and_list(
    dict_param: dict[str, int], list_param: list[dict[str, int]]
) -> dict[str, list]:
    """For testing typed dict and list type annotations."""
    list_param.append(dict_param)
    return {"": list_param}


def nested_model(a: NestedModels) -> dict[str, NestedModels]:
    """For testing methods using nested models."""
    return {"": a}


def list_model_result() -> list[ListResultModel]:
    """Function returning a list of a model."""
    return []


def no_annotations(a, b):  # type: ignore
    """To test discover for poorly written functions."""
    return a + b


def method_with_properties() -> None:
    """Method to test other method properties."""
    return None


def method_using_complex_objects(
    date_field: datetime.date,
    time_field: datetime.time,
    datetime_field: datetime.datetime,
    timedelta_field: datetime.timedelta,
    decimal_field: Decimal,
) -> ComplexObjects:
    """Method to test schema generation for complex objects."""
    return ComplexObjects(
        date_field=date_field,
        time_field=time_field,
        datetime_field=datetime_field,
        timedelta_field=timedelta_field,
        decimal_field=decimal_field,
    )
