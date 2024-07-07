"""Test Python enums to JSON Schema enums."""

import enum
import json
from typing import Optional

from openrpc import RPCServer
from tests import util
from tests.util import get_response

rpc = RPCServer(title="Test Enums", version="1.0.0", debug=True)


class EnumExample(enum.Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


class EnumExampleWithNull(enum.Enum):
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
        == "1 validation error for enum_test_func_params"
    )


def test_enum_optional_param() -> None:
    e_rpc = RPCServer(debug=True)

    class EnumOnlyUsedAsParam(enum.Enum):
        """Enum only ever used as a parameter type."""

        OPTION = enum.auto()

    # noinspection PyUnusedLocal
    @e_rpc.method()
    def method(param: Optional[EnumOnlyUsedAsParam]) -> None:  # noqa: ARG001
        """Pass."""

    req = util.get_request("rpc.discover")
    resp = util.get_response(e_rpc, req)

    assert "EnumOnlyUsedAsParam" in resp["result"]["components"]["schemas"]
