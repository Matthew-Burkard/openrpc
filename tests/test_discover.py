"""Test the generated "rpc.discover" method."""

import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional, Union

from jsonrpcobjects.objects import Request
from pydantic import BaseModel, Field

from openrpc import (
    Contact,
    Depends,
    Error,
    ExternalDocumentation,
    License,
    Link,
    ParamStructure,
    RPCServer,
    Server,
)
from openrpc._common import get_schema
from openrpc._objects import OpenRPC
from tests.util import Vector3, dump, resolve, validate_references


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
    list_field: list  # type: ignore
    list_str: list[str]
    list_list: list[list]  # type: ignore
    list_list_int: list[list[int]]
    list_union: list[Union[str, int]]
    tuple_field: tuple  # type: ignore
    tuple_str: tuple[str]
    tuple_tuple: tuple[tuple]  # type: ignore
    tuple_tuple_int: tuple[tuple[int]]
    tuple_union: tuple[Union[str, int]]
    tuple_int_str_none: tuple[int, str, None]
    set_str: set[str]
    set_union: set[Union[str, int]]
    dict_field: dict  # type: ignore
    dict_str: dict[str, str]
    dict_dict: dict[str, dict]  # type: ignore
    dict_int_keys: dict[int, str]
    dict_union: dict[str, Union[str, int]]


def test_open_rpc_info() -> None:
    rpc = RPCServer(
        title="Test OpenRPC",
        version="1.0.0",
        debug=True,
        description="description",
        terms_of_service="terms_of_service",
        contact=Contact(),
        license_=License(name="name"),
    )
    rpc.method()(increment)
    rpc.method()(get_distance)
    rpc.method()(return_none)
    rpc.method()(default_value)
    rpc.method()(take_any_get_any)
    rpc.method()(dict_and_list)  # type: ignore
    rpc.method()(nested_model)
    rpc.method()(typed_dict_and_list)  # type: ignore
    rpc.method()(list_model_result)
    rpc.method()(no_annotations)  # type: ignore
    rpc.title = rpc.title or "Test OpenRPC"
    rpc.version = rpc.version or "1.0.0"
    rpc.description = rpc.description or "Testing rpc.discover"
    rpc.terms_of_service = rpc.terms_of_service or "Coffee"
    rpc.contact = rpc.contact or Contact(name="mocha")
    rpc.license_ = rpc.license_ or License(name="AGPLv3")
    rpc.servers = rpc.servers or Server(name="default", url="localhost")
    request = Request(id=1, method="rpc.discover")
    resp = json.loads(rpc.process_request(request.model_dump_json()))  # type: ignore
    discover_result = resp["result"]
    assert "1.2.6" == discover_result["openrpc"]  # noqa: SIM300
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
        external_docs=ExternalDocumentation(url=url),
        deprecated=True,
        servers=[Server(name="Server", url=url)],
        errors=[Error(code=0, message="Error Message")],
        links=[Link(name="Link")],
        param_structure=ParamStructure.BY_NAME,
    )(method_with_properties)
    method = rpc.discover()["methods"][0]
    assert method["name"] == "method_with_properties"
    assert method["summary"] == "Method to test other method properties."
    assert method["externalDocs"] == {"url": url}
    assert method["deprecated"] is True
    assert method["servers"] == [{"name": "Server", "url": url}]
    assert method["errors"] == [{"code": 0, "message": "Error Message"}]
    assert method["links"] == [{"name": "Link"}]
    assert method["paramStructure"] is ParamStructure.BY_NAME


def test_lists() -> None:
    rpc = _rpc()
    rpc.method()(increment)
    doc = OpenRPC(**rpc.discover())
    # Examples
    assert doc.methods[0].examples is not None
    examples = dump(doc.methods[0].examples[0])
    assert examples == {
        "params": [{"name": "numbers", "value": [1]}],
        "result": {"value": [1]},
    }
    # Params
    expected_param_schema = {
        "type": "array",
        "items": {"anyOf": [{"type": "integer"}, {"type": "number"}]},
        "title": "Numbers",
    }
    param_schema = doc.methods[0].params[0].schema_
    assert dump(param_schema) == expected_param_schema
    # Result
    expected_result = {
        "type": "array",
        "items": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
        "title": "Result",
    }
    result_schema = doc.methods[0].result.schema_
    assert dump(result_schema) == expected_result


def test_schema_params() -> None:
    rpc = _rpc()
    rpc.method()(get_distance)
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    model_example = {
        "enum_field": EnumAsModelField.A,
        "vanilla_model": {"x": 1.0, "y": 1.0, "z": 1.0},
        "x": 1.0,
        "y": 1.0,
    }
    # Examples
    assert method.examples is not None
    example = method.examples[0]
    assert example.params is not None
    assert dump(example.params[0]) == {"name": "position", "value": model_example}
    assert dump(example.params[1]) == {"name": "target", "value": model_example}
    assert example.result is not None
    assert dump(example.result) == {"value": model_example}
    # Params
    p1 = method.params[0]
    p1_schema = dump(resolve(p1.schema_, doc.components))
    assert p1_schema["properties"] == {
        "x": {"title": "X", "type": "number"},
        "y": {"title": "Y", "type": "number"},
        "vanilla_model": {"$ref": "#/components/schemas/Vector3"},
        "enum_field": {"$ref": "#/components/schemas/EnumAsModelField"},
    }


def test_defaults() -> None:
    rpc = _rpc()
    rpc.method()(default_value)
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    # Examples
    assert method.examples is not None
    assert method.examples[0].model_dump(exclude_none=True) == {
        "params": [
            {"name": "a", "value": 2},
            {"name": "b", "value": 0.99792458},
            {"name": "c", "value": "c"},
        ],
        "result": {"value": "string"},
    }
    # Params
    assert method.model_dump(exclude_unset=True, by_alias=True)["params"] == [
        {
            "name": "a",
            "schema": {"title": "A", "type": "integer", "default": 2},
            "required": False,
        },
        {
            "name": "b",
            "schema": {"title": "B", "type": "number", "default": 0.99792458},
            "required": False,
        },
        {
            "name": "c",
            "schema": {"title": "C", "type": "string", "default": "c"},
            "required": False,
        },
    ]
    # Result
    assert method.result.model_dump(exclude_unset=True, by_alias=True) == {
        "name": "result",
        "schema": {"title": "Result", "type": "string"},
    }


def test_return_none() -> None:
    rpc = _rpc()
    rpc.method()(return_none)
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    # Examples
    assert method.examples is not None
    assert dump(method.examples[0]) == {
        "params": [{"name": "optional_param", "value": "string"}],
        "result": {"value": None},
    }
    # Params
    param_schema = dump(method.params[0].schema_)
    assert param_schema == {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "title": "Optional Param",
    }
    # Result
    result_schema = dump(method.result.schema_)
    assert result_schema == {"title": "Result", "type": "null"}


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
    assert method["result"] == {"name": "result", "schema": {"title": "Result"}}


def test_no_annotations() -> None:
    rpc = _rpc()
    rpc.method()(no_annotations)  # type: ignore
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
    assert method["result"] == {"name": "result", "schema": {"title": "Result"}}


def test_complex_objects() -> None:
    rpc = _rpc()
    rpc.method()(method_using_complex_objects)
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    # Examples
    assert bool(method.examples)
    assert bool(method.examples[0].params)
    assert method.examples[0].params[0].name == "date_field"
    # Params
    assert dump(method.params[0].schema_) == {
        "format": "date",
        "title": "Date Field",
        "type": "string",
    }
    assert dump(method.params[1].schema_) == {
        "format": "time",
        "title": "Time Field",
        "type": "string",
    }
    assert dump(method.params[2].schema_) == {
        "format": "date-time",
        "title": "Datetime Field",
        "type": "string",
    }
    assert dump(method.params[3].schema_) == {
        "format": "duration",
        "title": "Timedelta Field",
        "type": "string",
    }
    assert dump(method.params[4].schema_) == {
        "anyOf": [{"type": "number"}, {"type": "string"}],
        "title": "Decimal Field",
    }
    # Result
    assert dump(method.params[4].schema_) == {
        "anyOf": [{"type": "number"}, {"type": "string"}],
        "title": "Decimal Field",
    }
    validate_references(method.result.schema_, doc.components)


def test_collections() -> None:
    rpc = _rpc()
    rpc.method()(method_using_collections)  # type: ignore
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]

    # Params
    assert dump(method.params[0].schema_) == {
        "items": {},
        "title": "List Field",
        "type": "array",
    }
    assert dump(method.params[1].schema_) == {
        "items": {"type": "string"},
        "title": "List Str",
        "type": "array",
    }
    schema = method.params[2].schema_
    assert dump(schema) == {
        "title": "List List",
        "items": {"items": {}, "type": "array"},
        "type": "array",
    }
    assert dump(get_schema(get_schema(method.params[3].schema_).items)) == {
        "items": {"type": "integer"},
        "type": "array",
    }
    assert dump(method.params[4].schema_) == {
        "title": "List Union",
        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        "type": "array",
    }
    # Tuples
    assert dump(method.params[5].schema_) == {
        "items": {},
        "title": "Tuple Field",
        "type": "array",
    }
    assert dump(method.params[6].schema_) == {
        "maxItems": 1,
        "minItems": 1,
        "prefixItems": [{"type": "string"}],
        "title": "Tuple Str",
        "type": "array",
    }

    assert dump(get_schema(method.params[7].schema_)) == {
        "maxItems": 1,
        "minItems": 1,
        "prefixItems": [{"items": {}, "type": "array"}],
        "title": "Tuple Tuple",
        "type": "array",
    }

    assert dump(method.params[8].schema_) == {
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
    }

    assert dump(method.params[9].schema_) == {
        "maxItems": 1,
        "minItems": 1,
        "prefixItems": [{"anyOf": [{"type": "string"}, {"type": "integer"}]}],
        "title": "Tuple Union",
        "type": "array",
    }
    assert dump(method.params[10].schema_) == {
        "maxItems": 3,
        "minItems": 3,
        "prefixItems": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
        "title": "Tuple Int Str None",
        "type": "array",
    }
    # Sets
    assert dump(method.params[11].schema_) == {
        "items": {"type": "string"},
        "title": "Set Str",
        "type": "array",
        "uniqueItems": True,
    }
    assert dump(method.params[12].schema_) == {
        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        "title": "Set Union",
        "type": "array",
        "uniqueItems": True,
    }
    # Dictionaries
    assert dump(method.params[13].schema_) == {
        "title": "Dict Field",
        "type": "object",
    }
    assert dump(method.params[14].schema_) == {
        "additionalProperties": {"type": "string"},
        "title": "Dict Str",
        "type": "object",
    }
    assert dump(method.params[15].schema_) == {
        "additionalProperties": {"type": "object"},
        "title": "Dict Dict",
        "type": "object",
    }
    assert dump(method.params[16].schema_) == {
        "additionalProperties": {"type": "string"},
        "title": "Dict Int Keys",
        "type": "object",
    }
    assert dump(method.params[17].schema_) == {
        "additionalProperties": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        "title": "Dict Union",
        "type": "object",
    }


def test_method_union_model() -> None:
    rpc = _rpc()
    rpc.method()(method_union_model)
    doc = OpenRPC(**rpc.discover())
    validate_references(doc.methods[0].result.schema_, doc.components)


def test_recursive_schemas() -> None:
    rpc = _rpc()
    rpc.method()(nested_model)
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    schema_properties = resolve(method.params[0].schema_, doc.components).properties
    assert schema_properties is not None
    recursive = get_schema(schema_properties["recursion"])
    any_of = recursive.any_of or []
    properties = resolve(any_of[0], doc.components).properties or {}
    assert properties["recursion"] == recursive


def test_param_descriptions() -> None:
    result_descriptions = [None, "The params."]
    for method in [param_descriptions, param_description_no_return]:
        rpc = _rpc()
        rpc.method()(method)
        doc = rpc.discover()
        assert doc["methods"][0]["params"][0]["description"] == (
            "First param, it has a long description that spans more than one line."
        )
        assert doc["methods"][0]["params"][1]["description"] == "Second param."
        assert doc["methods"][0]["params"][2]["description"] == "Third param."
        assert (
            doc["methods"][0]["result"].get("description") == result_descriptions.pop()
        )


def test_descriptions() -> None:
    rpc = _rpc()

    @rpc.method()
    def description() -> None:  # type: ignore
        """Method description.

        This method also has a lengthy description in addition to the
        summary line. It makes a point to span multiple lines for the sake
        of doing so.
        """

    @rpc.method()
    def description_w_params(_a: int) -> None:  # type: ignore
        """Method description.

        This method also has a lengthy description in addition to the
        summary line. It makes a point to span multiple lines for the sake
        of doing so.

        :param _a: An integer.
        """

    doc = rpc.discover()
    expected_description = (
        "This method also has a lengthy description in addition to the summary line. It"
        " makes a point to span multiple lines for the sake of doing so."
    )
    expected_first_line = "Method description."
    assert doc["methods"][0]["summary"] == expected_first_line
    assert doc["methods"][0]["description"] == expected_description
    assert doc["methods"][1]["summary"] == expected_first_line
    assert doc["methods"][1]["description"] == expected_description


def test_no_description() -> None:
    rpc = _rpc()

    @rpc.method()
    def no_description(_a: int) -> None:  # type: ignore
        """Summary line.

        :param _a: A param.
        """

    doc = rpc.discover()
    assert doc["methods"][0].get("description") is None


def test_schema_cleanup() -> None:
    rpc = _rpc()

    def add(a: int, b: int) -> int:
        return a + b

    rpc.method()(add)
    doc = rpc.discover()
    assert not doc["components"]["schemas"]


def _rpc() -> RPCServer:
    return RPCServer(title="Test OpenRPC", version="1.0.0", debug=True)


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def increment(
    numbers: list[Union[int, float]],  # noqa: ARG001
) -> list[Union[int, str]]:  # type: ignore
    """Collections and unions."""


# noinspection PyUnusedLocal
def get_distance(
    position: Vector2,  # noqa: ARG001
    target: Vector2,  # noqa: ARG001
) -> Vector2:  # type: ignore
    """Function with basic model annotations."""


# noinspection PyUnusedLocal
def default_value(
    a: int = 2,
    b: float = 0.99792458,
    c: str = "c",  # noqa: ARG001
) -> str:  # noqa: ARG001  # type: ignore
    """Function with default values for params."""


# noinspection PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:  # noqa: ARG001
    """Function with optional param that always returns None."""


# noinspection PyUnusedLocal
def take_any_get_any(
    any_param: Any,
    dep: str = Depends(lambda x: x),  # type: ignore  # noqa: ARG001
) -> Any:
    """Function that takes and returns any type, uses Dep argument."""


# noinspection PyUnusedLocal
def dict_and_list(  # type: ignore
    dict_param: dict,  # type: ignore
    list_param: list,  # type: ignore  # noqa: ARG001
) -> dict[str, list]:  # type: ignore
    """For testing dict and list type annotations."""


# noinspection PyUnusedLocal
def typed_dict_and_list(  # type: ignore
    dict_param: dict[str, int],
    list_param: list[dict[str, int]],  # noqa: ARG001
) -> dict[str, list]:  # type: ignore
    """For testing typed dict and list type annotations."""


# noinspection PyUnusedLocal
def nested_model(
    a: NestedModels,  # noqa: ARG001
) -> dict[str, NestedModels]:  # type: ignore
    """For testing methods using nested models."""


# noinspection PyUnusedLocal
def list_model_result() -> list[ListResultModel]:  # type: ignore
    """Function returning a list of a model."""


# noinspection PyUnusedLocal
def no_annotations(a, b):  # type: ignore  # noqa: ARG001
    """To test discover for poorly written functions."""


# noinspection PyUnusedLocal
def method_with_properties() -> None:
    """Method to test other method properties."""


# noinspection PyUnusedLocal
def method_using_complex_objects(
    date_field: datetime.date,  # noqa: ARG001
    time_field: datetime.time,  # noqa: ARG001
    datetime_field: datetime.datetime,  # noqa: ARG001
    timedelta_field: datetime.timedelta,  # noqa: ARG001
    decimal_field: Decimal,  # noqa: ARG001
) -> ComplexObjects:  # type: ignore
    """Method to test schema generation for complex objects."""


# noinspection PyUnusedLocal
def method_using_collections(
    list_field: list,  # type: ignore  # noqa: ARG001
    list_str: list[str],  # noqa: ARG001
    list_list: list[list],  # type: ignore  # noqa: ARG001
    list_list_int: list[list[int]],  # noqa: ARG001
    list_union: list[Union[str, int]],  # noqa: ARG001
    tuple_field: tuple,  # type: ignore  # noqa: ARG001
    tuple_str: tuple[str],  # noqa: ARG001
    tuple_tuple: tuple[tuple],  # type: ignore  # noqa: ARG001
    tuple_tuple_int: tuple[tuple[int]],  # noqa: ARG001
    tuple_union: tuple[Union[str, int]],  # noqa: ARG001
    tuple_int_str_none: tuple[int, str, None],  # noqa: ARG001
    set_str: set[str],  # noqa: ARG001
    set_union: set[Union[str, int]],  # noqa: ARG001
    dict_field: dict,  # type: ignore  # noqa: ARG001
    dict_str: dict[str, str],  # noqa: ARG001
    dict_dict: dict[str, dict],  # type: ignore  # noqa: ARG001
    dict_int_keys: dict[int, str],  # noqa: ARG001
    dict_union: dict[str, Union[str, int]],  # noqa: ARG001
) -> CollectionsModel:  # type: ignore
    """Method using collection types."""


# noinspection PyUnusedLocal
def method_union_model() -> Union[ComplexObjects, CollectionsModel, None]:
    """Method with union model."""


# noinspection PyUnusedLocal
def param_descriptions(
    a: int,
    b: int,
    c: int,  # noqa: ARG001
) -> tuple[int, int, int]:  # type: ignore
    """Method with param descriptions.

    :param a: First param, it has a long description that spans more
        than one line.
    :param b: Second param.
    :param c: Third param.
    :return: The params.
    """


# noinspection PyUnusedLocal
def param_description_no_return(
    a: int,
    b: int,
    c: int,  # noqa: ARG001
) -> tuple[int, int, int]:  # type: ignore
    """Method with param descriptions.

    :param a: First param, it has a long description that spans more
        than one line.
    :param b: Second param.
    :param c: Third param.
    """
