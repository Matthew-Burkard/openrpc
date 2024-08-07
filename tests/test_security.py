"""Unit tests for permissions."""

from typing import Mapping, Union

import pytest
from jsonrpcobjects.objects import ErrorResponse, ResultResponse

from openrpc import Depends, OAuth2, OAuth2Flow, OAuth2FlowType, RPCServer
from openrpc._objects import APIKeyAuth, BearerAuth
from tests import util

security: Mapping[str, Union[OAuth2, BearerAuth, APIKeyAuth]] = {
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


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


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
        _headers: dict[str, str], user=Depends(middleware)  # noqa: B008
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
    response = util.parse_result_response(
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
        rpc.process_request(
            request, caller_details={"apikey": ["apple"], "oauth2": ["mocha"]}
        )
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
    response = util.parse_response(
        rpc.process_request(request, caller_details={"apikey": ["pickle"]})
    )
    assert isinstance(response, ResultResponse)
    assert response.result["components"]["x-securitySchemes"] == {
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
    assert response.result["methods"][1]["x-security"] == {
        "oauth2": ["coffee", "mocha"],
        "apikey": ["pickle"],
    }


def test_security_no_caller_details() -> None:
    def _security_function() -> dict[str, list[str]]:
        return {"apikey": ["pickle"]}

    no_cd_rpc = RPCServer(security_schemes=security)
    no_cd_rpc.method(security={"apikey": ["pickle"]})(add)
    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_error_response(no_cd_rpc.process_request(request))
    assert no_cd_rpc.security_function is None
    assert isinstance(response, ErrorResponse)
    assert response.error.message == "Permission error"

    no_cd_rpc.security_function = _security_function
    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_result_response(no_cd_rpc.process_request(request))
    expected = 4
    assert no_cd_rpc.security_function is not None
    assert response.result == expected


def test_security_only_depends() -> None:
    def _depends() -> dict[str, list[str]]:
        return {"apikey": ["pickle"]}

    def _security(
        depends: dict[str, list[str]] = Depends(_depends)  # noqa: B008
    ) -> dict[str, list[str]]:
        return depends

    only_depends_rpc = RPCServer(
        security_schemes=security, security_function=_security, debug=True
    )
    only_depends_rpc.method(security={"apikey": ["pickle"]})(add)
    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_result_response(only_depends_rpc.process_request(request))
    expected = 4
    assert response.result == expected


def test_nested_depends() -> None:
    counter = 0

    def _depends_a() -> int:
        nonlocal counter
        counter += 1
        return 5

    def _depends_b(a: int = Depends(_depends_a)) -> int:
        return a * 2

    def _rpc_method(a: int = Depends(_depends_a), b: int = Depends(_depends_b)) -> int:
        return a + b

    nested_depends_rpc = RPCServer(debug=True)
    nested_depends_rpc.method()(_rpc_method)
    request = '{"id": 1, "method": "_rpc_method", "jsonrpc": "2.0"}'
    response = util.parse_result_response(nested_depends_rpc.process_request(request))
    expected = 15
    assert counter == 1
    assert response.result == expected


@pytest.mark.asyncio
async def test_async_security_function() -> None:
    async def _awaitable_security(
        caller_details: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        return caller_details

    async_rpc = RPCServer(security_schemes=security, debug=True)
    async_rpc.method(security={"mocha": []})(add)

    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_response(await async_rpc.process_request_async(request))
    assert isinstance(response, ErrorResponse)
    assert response.error.message == "Permission error"

    async_rpc.security_function = _awaitable_security

    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_response(
        await async_rpc.process_request_async(request, caller_details={"coffee": []})
    )
    assert isinstance(response, ErrorResponse)
    assert response.error.message == "Permission error"

    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_result_response(
        await async_rpc.process_request_async(request, caller_details={"mocha": []})
    )
    expected = 4
    assert response.result == expected


@pytest.mark.asyncio
async def test_async_no_caller() -> None:
    async def _awaitable_security() -> dict[str, list[str]]:
        return {"a": []}

    async_rpc = RPCServer(
        security_schemes=security, security_function=_awaitable_security, debug=True
    )
    async_rpc.method(security={"a": []})(add)
    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_result_response(
        await async_rpc.process_request_async(request)
    )
    expected = 4
    assert response.result == expected


@pytest.mark.asyncio
async def test_nested_depends_async() -> None:
    counter = 0

    async def _depends_a() -> int:
        nonlocal counter
        counter += 1
        return 5

    async def _depends_b(a: int = Depends(_depends_a)) -> int:
        return a * 2

    async def _rpc_method(
        a: int = Depends(_depends_a), b: int = Depends(_depends_b)
    ) -> int:
        return a + b

    nested_depends_rpc = RPCServer(debug=True)
    nested_depends_rpc.method()(_rpc_method)
    request = '{"id": 1, "method": "_rpc_method", "jsonrpc": "2.0"}'
    response = util.parse_result_response(
        await nested_depends_rpc.process_request_async(request)
    )
    assert counter == 1
    expected = 15
    assert response.result == expected


def test_async_security_error() -> None:
    # noinspection PyUnusedLocal
    async def _security() -> dict[str, list[str]]: ...

    async_error_rpc = RPCServer(security_function=_security, debug=True)
    async_error_rpc.method(security={"a": []})(add)
    request = '{"id": 1, "method": "add", "params": [2, 2], "jsonrpc": "2.0"}'
    response = util.parse_response(async_error_rpc.process_request(request))
    assert isinstance(response, ErrorResponse)
    assert response.error.message == "Internal error"
