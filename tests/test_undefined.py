"""Tests for `Undefined` type."""
from typing import Optional

from openrpc import RPCServer, Undefined
from tests import util


rpc = RPCServer(debug=True)


@rpc.method()
def method(param: str = Undefined) -> bool:
    """Method with non-required param."""
    return param is Undefined


# noinspection PyUnusedLocal
@rpc.method()
def method_two(required: str, param: Optional[str] = Undefined) -> bool:
    """Method with required and non-required params."""
    return param is Undefined


def test_undefined() -> None:
    assert not Undefined
    request = util.get_request("method")
    response = util.parse_response(rpc.process_request(request))
    assert response.result is True
    request = util.get_request("method", '{"param": ""}')
    response = util.parse_response(rpc.process_request(request))
    assert response.result is False
    request = util.get_request("method", '[""]')
    response = util.parse_response(rpc.process_request(request))
    assert response.result is False


def test_undefined_with_required() -> None:
    request = util.get_request("method_two", '[""]')
    response = util.parse_response(rpc.process_request(request))
    assert response.result is True


def test_undefined_discover() -> None:
    param = rpc.discover()["methods"][0]["params"][0]
    assert param["required"] is False
    assert "default" not in param["schema"]
