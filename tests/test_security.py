"""Unit tests for permissions."""

from jsonrpcobjects.objects import ErrorResponse, ResultResponse

from openrpc import Depends, OAuth2, OAuth2Flow, OAuth2FlowType, RPCServer
from tests import util

security = {
    "oauth2": OAuth2(
        flows=[
            OAuth2Flow(
                type=OAuth2FlowType.AUTHORIZATION_CODE,
                authorizationUrl="http://localhost:8000/oauth",
                tokenUrl="http://localhost:8000/oauth.access",
                scopes={"coffee": "The coffee scope.", "mocha": "The mocha scope."},
            )
        ]
    )
}
rpc = RPCServer(security_schemes=security, security_function=lambda x: x, debug=True)


@rpc.method(security={"oauth2": ["coffee", "mocha"]})
def permission_method() -> None:
    """Method requiring a permission."""


@rpc.method(security={"oauth2": ["coffee", "mocha"], "apikey": ["pickle"]})
def multiple_schemes() -> None:
    """Method requiring one of multiple permissions."""


@rpc.method(security={"apikey": []})
def no_scopes() -> None:
    """Method requiring a permission with no scope."""


def test_security_depends() -> None:
    counter = 0

    def middleware(headers: dict[str, str]) -> str:
        """Middleware function."""
        nonlocal counter
        counter += 1
        return headers["user"]

    def security_function(
        _headers: dict[str, str], user=Depends(middleware)
    ) -> dict[str, list[str]]:
        """Typical security function."""
        return {"pizza": {"oauth2": ["coffee", "mocha"]}}[user]

    security_rpc = RPCServer(
        security_schemes=security, security_function=security_function, debug=True
    )

    @security_rpc.method(security={"oauth2": ["coffee", "mocha"]})
    def permission_method_with_depends(user: str = Depends(middleware)) -> str:
        """Method requiring a permission with `Depends`."""
        return user

    request = '{"id": 1, "method": "permission_method_with_depends", "jsonrpc": "2.0"}'
    response = util.parse_response(
        security_rpc.process_request(request, {"user": "pizza"})
    )
    assert response.result == "pizza"
    assert counter == 1


def test_deny() -> None:
    request = '{"id": 1, "method": "permission_method", "jsonrpc": "2.0"}'
    result = util.parse_response(rpc.process_request(request))
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, caller_details={"oauth2": ["coffee"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"


def test_permit() -> None:
    request = '{"id": 1, "method": "permission_method", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, caller_details={"oauth2": ["coffee", "mocha"]})
    )

    assert isinstance(result, ResultResponse)


def test_multiple_schemes_deny() -> None:
    request = '{"id": 1, "method": "multiple_schemes", "jsonrpc": "2.0"}'
    result = util.parse_response(rpc.process_request(request))
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, caller_details={"oauth2": ["coffee"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, caller_details={"oauth2": ["pickle"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"
    result = util.parse_response(
        rpc.process_request(request, caller_details={"apikey": ["coffee", "mocha"]})
    )
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"


def test_multiple_schemes_permit() -> None:
    request = '{"id": 1, "method": "multiple_schemes", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, caller_details={"apikey": ["pickle"]})
    )
    assert isinstance(result, ResultResponse)
    result = util.parse_response(
        rpc.process_request(request, caller_details={"oauth2": ["coffee", "mocha"]})
    )
    assert isinstance(result, ResultResponse)


def test_no_scopes() -> None:
    request = '{"id": 1, "method": "no_scopes", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, caller_details={"apikey": []})
    )
    assert isinstance(result, ResultResponse)
    result = util.parse_response(rpc.process_request(request))
    assert isinstance(result, ErrorResponse)
    assert result.error.message == "Permission error"


def test_security_discover() -> None:
    request = '{"id": 1, "method": "rpc.discover", "jsonrpc": "2.0"}'
    result = util.parse_response(
        rpc.process_request(request, caller_details={"apikey": ["pickle"]})
    )
    assert isinstance(result, ResultResponse)
    assert result.result["components"]["x-securitySchemes"] == {
        "oauth2": {
            "flows": [
                {
                    "authorizationUrl": "http://localhost:8000/oauth",
                    "scopes": {
                        "coffee": "The coffee scope.",
                        "mocha": "The mocha scope.",
                    },
                    "tokenUrl": "http://localhost:8000/oauth.access",
                    "type": "authorizationCode",
                }
            ],
            "type": "oauth2",
        }
    }
    assert result.result["methods"][1]["x-security"] == {
        "oauth2": ["coffee", "mocha"],
        "apikey": ["pickle"],
    }
