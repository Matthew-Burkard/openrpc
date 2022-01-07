"""Test deserializing union types."""
import json
import unittest
from typing import Union

from pydantic import BaseModel, StrictInt, StrictStr

from openrpc.server import RPCServer


# noinspection PyMissingOrEmptyDocstring
class CustomA(BaseModel):
    int_field: StrictInt


# noinspection PyMissingOrEmptyDocstring
class CustomB(BaseModel):
    str_field: StrictStr


# noinspection PyMissingOrEmptyDocstring
def func(c: Union[CustomA, CustomB]) -> bool:
    return isinstance(c, CustomA) or isinstance(c, CustomB)


class UnionsTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.rpc = RPCServer(title="Test Unions", version="1.0.0")
        super(UnionsTest, self).__init__(*args)

    def test_union_casting(self) -> None:
        self.rpc.method(func)
        req1 = {
            "id": 0,
            "method": "func",
            "params": [{"int_field": 1}],
            "jsonrpc": "2.0",
        }
        req2 = {
            "id": 0,
            "method": "func",
            "params": [{"str_field": "coffee"}],
            "jsonrpc": "2.0",
        }
        req3 = {
            "id": 0,
            "method": "func",
            "params": [{"int_field": 3.14}],
            "jsonrpc": "2.0",
        }
        res1 = json.loads(self.rpc.process_request(json.dumps(req1)))["result"]
        res2 = json.loads(self.rpc.process_request(json.dumps(req2)))["result"]
        res3 = json.loads(self.rpc.process_request(json.dumps(req3)))
        self.assertEqual(True, res1)
        self.assertEqual(True, res2)
        self.assertEqual("Internal error", res3["error"]["message"])
