"""Test Python enums to JSON Schema enums."""
import json
import unittest
from enum import Enum
from typing import Any

from openrpc import RPCServer


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


class EnumExampleWithNull(Enum):
    """If any field is None, "null" should be a valid type."""

    STR_OPTION = r'\"\\"'
    OPT_INT_OPTION = None


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def enum_test_func(ee: EnumExample) -> EnumExampleWithNull:
    assert isinstance(ee, EnumExample)
    return EnumExampleWithNull.STR_OPTION


class EnumTest(unittest.TestCase):
    def __init__(self, *args: Any) -> None:
        self.rpc = RPCServer(title="Test Enums", version="1.0.0")
        super(EnumTest, self).__init__(*args)

    def test_register_enum_using_method(self) -> None:
        self.rpc.method()(enum_test_func)
        rpc_doc = self.rpc.discover()
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

        self.assertEqual(param_schema, components["EnumExample"])
        self.assertEqual(result_schema, components["EnumExampleWithNull"])
        self.assertEqual(params, rpc_doc["methods"][0]["params"])
        self.assertEqual(result, rpc_doc["methods"][0]["result"])

    def test_calling_enums_method(self) -> None:
        self.rpc.method()(enum_test_func)
        req = {
            "id": 0,
            "method": "enum_test_func",
            "params": [3],
            "jsonrpc": "2.0",
        }
        res = json.loads(self.rpc.process_request(json.dumps(req)))
        self.assertEqual(EnumExampleWithNull.STR_OPTION.value, res["result"])

    def test_calling_enums_method_with_bar_param(self) -> None:
        self.rpc.method()(enum_test_func)
        req = {
            "id": 0,
            "method": "enum_test_func",
            "params": [5],
            "jsonrpc": "2.0",
        }
        res = json.loads(self.rpc.process_request(json.dumps(req)))
        self.assertEqual(
            "Failed to deserialize request param [5] to type [<enum 'EnumExample'>]",
            res["error"]["data"],
        )
