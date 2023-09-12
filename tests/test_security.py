"""Unit tests for permissions."""
from jsonrpcobjects.objects import ErrorResponse, ResultResponse

from openrpc import RPCServer
from tests import util

rpc = RPCServer()


@rpc.method(security={"oauth2": ["coffee", "mocha"]})
def permission_method() -> None:
    """Method requiring a permission."""


@rpc.method(security={"oauth2": ["coffee", "mocha"], "apikey": ["pickle"]})
def multiple_schemes() -> None:
    """Method requiring a permission."""


def test_deny() -> None:
    request = '{"id": 1, "method": "permission_method", "jsonrpc": "2.0"}'
    result = util.parse_response(rpc.process_request(request))
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, security={"oauth2": ["coffee"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"


def test_permit() -> None:
    request = '{"id": 1, "method": "permission_method", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, security={"oauth2": ["coffee", "mocha"]})
    )
    assert isinstance(result, ResultResponse)


def test_multiple_schemes_deny() -> None:
    request = '{"id": 1, "method": "multiple_schemes", "jsonrpc": "2.0"}'
    result = util.parse_response(rpc.process_request(request))
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, security={"oauth2": ["coffee"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, security={"oauth2": ["pickle"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, security={"apikey": ["coffee", "mocha"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"


def test_multiple_schemes_permit() -> None:
    request = '{"id": 1, "method": "multiple_schemes", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, security={"apikey": ["pickle"]})
    )
    assert isinstance(result, ResultResponse)
    result = util.parse_response(
        rpc.process_request(request, security={"oauth2": ["coffee", "mocha"]})
    )
    assert isinstance(result, ResultResponse)


def test_security_discover() -> None:
    pass
