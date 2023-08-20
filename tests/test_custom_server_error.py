"""OpenRPC custom JSON RPC errors tests."""
from typing import Any

from jsonrpcobjects.errors import JSONRPCError
from jsonrpcobjects.objects import DataError, ParamsRequest

from openrpc import RPCServer
from tests.util import get_response

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


def test_custom_error() -> None:
    params = {"a": 0, "b": 0}
    req = ParamsRequest(id=1, method="divide", params=params).model_dump_json()
    error = get_response(rpc, req)["error"]
    assert error["message"] == custom_error_object.message
    assert error["code"] == custom_error_object.code
    assert error["data"] == params
