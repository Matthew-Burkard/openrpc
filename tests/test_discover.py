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


class CollectionsModel(BaseModel):
    list_field: list
    list_str: list[str]
    list_list: list[list]
    list_list_int: list[list[int]]
    list_union: list[Union[str, int]]
    tuple_field: tuple
    tuple_str: tuple[str]
    tuple_tuple: tuple[tuple]
    tuple_tuple_int: tuple[tuple[int]]
    tuple_union: tuple[Union[str, int]]
    tuple_int_str_none: tuple[int, str, None]
    set_str: set[str]
    set_union: set[Union[str, int]]
    dict_field: dict
    dict_str: dict[str, str]
    dict_dict: dict[str, dict]
    dict_int_keys: dict[int, str]
    dict_union: dict[str, Union[str, int]]


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
                "title": "Numbers",
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
            "title": "Result",
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
                {"name": "a", "value": 2},
                {"name": "b", "value": 0.99792458},
                {"name": "c", "value": "c"},
            ],
            "result": {"value": "string"},
        }
    ]
    # Params
    assert method["params"] == [
        {
            "name": "a",
            "required": False,
            "schema": {"default": 2, "title": "A", "type": "integer"},
        },
        {
            "name": "b",
            "required": False,
            "schema": {"default": 0.99792458, "title": "B", "type": "number"},
        },
        {
            "name": "c",
            "required": False,
            "schema": {"default": "c", "title": "C", "type": "string"},
        },
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"title": "Result", "type": "string"},
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
            "required": True,
            "schema": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "title": "Optional Param",
            },
        }
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"title": "Result", "type": "null"},
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
    assert method["params"] == [
        {"name": "any_param", "required": True, "schema": {"title": "Any Param"}}
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"title": "Result"},
    }


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
        {"name": "a", "required": True, "schema": {"title": "A"}},
        {"name": "b", "required": True, "schema": {"title": "B"}},
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"title": "Result"},
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
            "schema": {"format": "date", "title": "Date Field", "type": "string"},
        },
        {
            "name": "time_field",
            "required": True,
            "schema": {"format": "time", "title": "Time Field", "type": "string"},
        },
        {
            "name": "datetime_field",
            "required": True,
            "schema": {
                "format": "date-time",
                "title": "Datetime Field",
                "type": "string",
            },
        },
        {
            "name": "timedelta_field",
            "required": True,
            "schema": {
                "format": "duration",
                "title": "Timedelta Field",
                "type": "string",
            },
        },
        {
            "name": "decimal_field",
            "required": True,
            "schema": {
                "anyOf": [{"type": "number"}, {"type": "string"}],
                "title": "Decimal Field",
            },
        },
    ]
    # Result
    assert method["result"] == {
        "name": "result",
        "required": True,
        "schema": {"$ref": "#/components/schemas/ComplexObjects"},
    }


def test_collections() -> None:
    rpc = _rpc()
    rpc.method()(method_using_collections)
    method = rpc.discover()["methods"][0]

    # Params
    # Lists
    assert method["params"][0] == {
        "name": "list_field",
        "required": True,
        "schema": {"items": {}, "title": "List Field", "type": "array"},
    }
    assert method["params"][1] == {
        "name": "list_str",
        "required": True,
        "schema": {"items": {"type": "string"}, "title": "List Str", "type": "array"},
    }
    assert method["params"][2] == {
        "name": "list_list",
        "required": True,
        "schema": {
            "items": {"items": {}, "type": "array"},
            "title": "List List",
            "type": "array",
        },
    }
    assert method["params"][3] == {
        "name": "list_list_int",
        "required": True,
        "schema": {
            "items": {"items": {"type": "integer"}, "type": "array"},
            "title": "List List Int",
            "type": "array",
        },
    }
    assert method["params"][4] == {
        "name": "list_union",
        "required": True,
        "schema": {
            "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            "title": "List Union",
            "type": "array",
        },
    }
    # Tuples
    assert method["params"][5] == {
        "name": "tuple_field",
        "required": True,
        "schema": {"items": {}, "title": "Tuple Field", "type": "array"},
    }
    assert method["params"][6] == {
        "name": "tuple_str",
        "required": True,
        "schema": {
            "maxItems": 1,
            "minItems": 1,
            "prefixItems": [{"type": "string"}],
            "title": "Tuple Str",
            "type": "array",
        },
    }
    assert method["params"][7] == {
        "name": "tuple_tuple",
        "required": True,
        "schema": {
            "maxItems": 1,
            "minItems": 1,
            "prefixItems": [{"items": {}, "type": "array"}],
            "title": "Tuple Tuple",
            "type": "array",
        },
    }
    assert method["params"][8] == {
        "name": "tuple_tuple_int",
        "required": True,
        "schema": {
            "maxItems": 1,
            "minItems": 1,
            "prefixItems": [
                {
                    "maxItems": 1,
                    "minItems": 1,
                    "prefixItems": [{"type": "integer"}],
                    "type": "array",
                }
            ],
            "title": "Tuple Tuple Int",
            "type": "array",
        },
    }
    assert method["params"][9] == {
        "name": "tuple_union",
        "required": True,
        "schema": {
            "maxItems": 1,
            "minItems": 1,
            "prefixItems": [{"anyOf": [{"type": "string"}, {"type": "integer"}]}],
            "title": "Tuple Union",
            "type": "array",
        },
    }
    assert method["params"][10] == {
        "name": "tuple_int_str_none",
        "required": True,
        "schema": {
            "maxItems": 3,
            "minItems": 3,
            "prefixItems": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
            "title": "Tuple Int Str None",
            "type": "array",
        },
    }
    # Sets
    assert method["params"][11] == {
        "name": "set_str",
        "required": True,
        "schema": {
            "items": {"type": "string"},
            "title": "Set Str",
            "type": "array",
            "uniqueItems": True,
        },
    }
    assert method["params"][12] == {
        "name": "set_union",
        "required": True,
        "schema": {
            "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            "title": "Set Union",
            "type": "array",
            "uniqueItems": True,
        },
    }
    # Dictionaries
    assert method["params"][13] == {
        "name": "dict_field",
        "required": True,
        "schema": {"title": "Dict Field", "type": "object"},
    }
    assert method["params"][14] == {
        "name": "dict_str",
        "required": True,
        "schema": {
            "additionalProperties": {"type": "string"},
            "title": "Dict Str",
            "type": "object",
        },
    }
    assert method["params"][15] == {
        "name": "dict_dict",
        "required": True,
        "schema": {
            "additionalProperties": {"type": "object"},
            "title": "Dict Dict",
            "type": "object",
        },
    }
    assert method["params"][16] == {
        "name": "dict_int_keys",
        "required": True,
        "schema": {
            "additionalProperties": {"type": "string"},
            "title": "Dict Int Keys",
            "type": "object",
        },
    }
    assert method["params"][17] == {
        "name": "dict_union",
        "required": True,
        "schema": {
            "additionalProperties": {
                "anyOf": [{"type": "string"}, {"type": "integer"}]
            },
            "title": "Dict Union",
            "type": "object",
        },
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


def method_using_collections(
    list_field: list,
    list_str: list[str],
    list_list: list[list],
    list_list_int: list[list[int]],
    list_union: list[Union[str, int]],
    tuple_field: tuple,
    tuple_str: tuple[str],
    tuple_tuple: tuple[tuple],
    tuple_tuple_int: tuple[tuple[int]],
    tuple_union: tuple[Union[str, int]],
    tuple_int_str_none: tuple[int, str, None],
    set_str: set[str],
    set_union: set[Union[str, int]],
    dict_field: dict,
    dict_str: dict[str, str],
    dict_dict: dict[str, dict],
    dict_int_keys: dict[int, str],
    dict_union: dict[str, Union[str, int]],
) -> CollectionsModel:
    """Method using collection types."""
    return CollectionsModel(
        list_field=list_field,
        list_str=list_str,
        list_list=list_list,
        list_list_int=list_list_int,
        list_union=list_union,
        tuple_field=tuple_field,
        tuple_str=tuple_str,
        tuple_tuple=tuple_tuple,
        tuple_tuple_int=tuple_tuple_int,
        tuple_union=tuple_union,
        tuple_int_str_none=tuple_int_str_none,
        set_str=set_str,
        set_union=set_union,
        dict_field=dict_field,
        dict_str=dict_str,
        dict_dict=dict_dict,
        dict_int_keys=dict_int_keys,
        dict_union=dict_union,
    )
