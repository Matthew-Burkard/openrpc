"""Test Python enums to JSON Schema enums."""
import unittest
from enum import Enum

from pydantic import BaseModel

from openrpc.server import RPCServer


class Model(BaseModel):
    """Example type for the enum."""

    int_field: int


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


class EnumClassFieldExample(Enum):
    """Enum with a field of a custom class type."""

    CLASS_OPTION = Model(int_field=1)


class EnumExampleWithNull(Enum):
    """If any field is null "null" should be a valid type."""

    STR_OPTION = r'\"\\"'
    OPT_INT_OPTION = None


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def enum_test_func(ee: EnumExample, ecf: EnumClassFieldExample) -> EnumExampleWithNull:
    assert isinstance(ee, EnumExample)
    assert isinstance(ecf, EnumClassFieldExample)
    return EnumExampleWithNull.STR_OPTION


class EnumTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.rpc = RPCServer(title="Test JSON RPC", version="1.0.0")
        super(EnumTest, self).__init__(*args)

    def test_register_enum_using_method(self) -> None:
        self.rpc.method(enum_test_func)
        params = [
            {
                "name": "ee",
                "schema": {"enum": [3, 'A string with a "']},
                "required": True,
            },
            {"name": "ecf", "schema": {"enum": [{"int_field": 1}]}, "required": True},
        ]
        result = {
            "name": "result",
            "schema": {"enum": ['\\"\\\\"', None]},
            "required": True,
        }
        res = self.rpc.discover()
        print(res)
        self.assertEqual(params, res["methods"][0]["params"])
        self.assertEqual(result, res["methods"][0]["result"])
