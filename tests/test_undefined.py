"""Tests for `Undefined` type."""
from openrpc import RPCServer, Undefined
from tests import util


rpc = RPCServer(debug=True)


@rpc.method()
def method(param: str = Undefined) -> bool:
    """Method with non-required param."""
    return param is Undefined


def test_undefined() -> None:
    assert not Undefined
    request = '{"id": 1, "method": "method", "jsonrpc": "2.0"}'
    response = util.parse_response(rpc.process_request(request))
    assert response.result is True
    request = '{"id": 1, "method": "method", "params": {"param": ""}, "jsonrpc": "2.0"}'
    response = util.parse_response(rpc.process_request(request))
    assert response.result is False
    request = '{"id": 1, "method": "method", "params": [""], "jsonrpc": "2.0"}'
    response = util.parse_response(rpc.process_request(request))
    assert response.result is False


def test_undefined_discover() -> None:
    param = rpc.discover()["methods"][0]["params"][0]
    assert param["required"] is False
    assert "default" not in param["schema"]
