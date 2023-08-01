"""OpenRPC custom JSON RPC errors tests."""
import json
import unittest
from typing import Any

from jsonrpcobjects.errors import JSONRPCError
from jsonrpcobjects.objects import DataError, ParamsRequest

from openrpc import RPCServer

rpc = RPCServer(title="Test Errors", version="1.0.0", debug=True)
custom_error_object = DataError(code=-32001, message="Cannot divide by zero", data={})


class DivideByZeroRPCError(JSONRPCError):
    """Custom JSON RPC Server Error."""

    def __init__(self, params: dict[str, Any]) -> None:
        error = custom_error_object
        error.data = params
        super(DivideByZeroRPCError, self).__init__(error)


@rpc.method()
def divide(a: float, b: float) -> None:
    """Test custom server error."""
    raise DivideByZeroRPCError({"a": a, "b": b})


class DecoratorTest(unittest.TestCase):
    def test_custom_error(self) -> None:
        params = {"a": 0, "b": 0}
        req = ParamsRequest(id=1, method="divide", params=params).model_dump_json()
        error = json.loads(rpc.process_request(req))["error"]
        self.assertEqual(custom_error_object.message, error["message"])
        self.assertEqual(custom_error_object.code, error["code"])
        self.assertEqual(params, error["data"])
