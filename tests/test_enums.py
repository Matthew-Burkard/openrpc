"""Test Python enums to JSON Schema enums."""
import json
from enum import Enum

from openrpc import RPCServer
from tests.util import get_response

rpc = RPCServer(title="Test Enums", version="1.0.0", debug=True)


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


class EnumExampleWithNull(Enum):
    """If any field is None, "null" should be a valid type."""

    STR_OPTION = r'\"\\"'
    OPT_INT_OPTION = None


@rpc.method()
def enum_test_func(ee: EnumExample) -> EnumExampleWithNull:
    """Function with Enum param and result."""
    assert isinstance(ee, EnumExample)
    return EnumExampleWithNull.STR_OPTION


def test_register_enum_using_method() -> None:
    rpc_doc = rpc.discover()
    components = rpc_doc["components"]["schemas"]

    # Param expectations.
    param_schema = {
        "description": "Each type for options should get a JSON Schema type.",
        "enum": [3, 'A string with a "'],
        "title": "EnumExample",
    }
    params = [
        {
            "name": "ee",
            "schema": {"$ref": "#/components/schemas/EnumExample"},
            "required": True,
        }
    ]
    # Result expectations.
    result_schema = {
        "description": 'If any field is None, "null" should be a valid type.',
        "enum": ['\\"\\\\"', None],
        "title": "EnumExampleWithNull",
    }
    result = {
        "name": "result",
        "schema": {"$ref": "#/components/schemas/EnumExampleWithNull"},
        "required": True,
    }

    assert components["EnumExample"] == param_schema
    assert components["EnumExampleWithNull"] == result_schema
    assert rpc_doc["methods"][0]["params"] == params
    assert rpc_doc["methods"][0]["result"] == result


def test_calling_enums_method() -> None:
    req = {
        "id": 0,
        "method": "enum_test_func",
        "params": [3],
        "jsonrpc": "2.0",
    }
    res = get_response(rpc, json.dumps(req))
    assert res["result"] == EnumExampleWithNull.STR_OPTION.value


def test_calling_enums_method_with_bar_param() -> None:
    req = {
        "id": 0,
        "method": "enum_test_func",
        "params": [5],
        "jsonrpc": "2.0",
    }
    res = get_response(rpc, json.dumps(req))
    assert (
        res["error"]["data"].split("\n")[0]
        == "1 validation error for enum_test_funcParams"
    )
