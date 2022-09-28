"""OpenRPC custom JSON RPC errors tests."""
import json
import unittest
from typing import Any

from jsonrpcobjects.errors import JSONRPCError
from jsonrpcobjects.objects import ErrorObjectData, RequestObjectParams

from openrpc import RPCServer

rpc = RPCServer(title="Test Errors", version="1.0.0")
custom_error_object = ErrorObjectData(code=-32001, message="Cannot divide by zero")


class DivideByZeroRPCError(JSONRPCError):
    """Custom JSON RPC Server Error."""

    def __init__(self, params: dict[str, Any]) -> None:
        error = custom_error_object
        error.data = params
        super(DivideByZeroRPCError, self).__init__(error)


@rpc.method
def divide(a: float, b: float) -> None:
    """Test custom server error."""
    if a == 0 or b == 0:
        raise DivideByZeroRPCError({"a": a, "b": b})


class DecoratorTest(unittest.TestCase):
    def test_custom_error(self) -> None:
        params = {"a": 0, "b": 0}
        req = RequestObjectParams(id=1, method="divide", params=params).json()
        error = json.loads(rpc.process_request(req))["error"]
        self.assertEqual(custom_error_object.message, error["message"])
        self.assertEqual(custom_error_object.code, error["code"])
        self.assertEqual(params, error["data"])
