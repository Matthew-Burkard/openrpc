"""Tests for `Undefined` type."""

import sys
from typing import Optional, Union

from openrpc import RPCServer, Undefined
from tests import util


def test_undefined() -> None:
    rpc = RPCServer(debug=True)

    @rpc.method()
    def method(  # pyright: ignore[reportUnusedFunction]
        param: str = Undefined,  # pyright: ignore[reportArgumentType]
    ) -> bool:
        """Method with non-required param."""
        return param is Undefined

    request = util.get_request("method")
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is True
    request = util.get_request("method", '{"param": ""}')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is False
    request = util.get_request("method", '[""]')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is False


def test_undefined_type() -> None:
    rpc = RPCServer(debug=True)

    @rpc.method()
    def undefined_type(  # pyright: ignore[reportUnusedFunction]
        param: Union[Undefined, str],
    ) -> bool:
        """Method using undefined as a parameter type."""
        return param is Undefined

    request = util.get_request("undefined_type")
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is True
    request = util.get_request("undefined_type", '{"param": ""}')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is False
    request = util.get_request("undefined_type", '[""]')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is False


def test_undefined_with_required() -> None:
    rpc = RPCServer(debug=True)

    # noinspection PyUnusedLocal
    @rpc.method()
    def method(  # pyright: ignore[reportUnusedFunction]
        _req: str,
        param: Optional[str] = Undefined,  # pyright: ignore[reportArgumentType]
    ) -> bool:
        """Method with required and non-required params."""
        return param is Undefined

    request = util.get_request("method", '[""]')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is True


def test_undefined_discover() -> None:
    rpc = RPCServer(debug=True)

    @rpc.method()
    def method(  # pyright: ignore[reportUnusedFunction]
        param: str = Undefined,  # pyright: ignore[reportArgumentType, reportUnusedParameter]
    ) -> bool:  # pyright: ignore[reportReturnType]
        """Method with non-required param."""

    schema_param = rpc.discover()["methods"][0]["params"][0]
    assert schema_param["required"] is False
    assert "default" not in schema_param["schema"]


def test_310_union() -> None:
    if sys.version_info < (3, 10):
        return
    rpc = RPCServer(debug=True)  # pyright: ignore[reportUnreachable]

    @rpc.method()
    def method310(param: int | None | Undefined) -> bool:  # noqa: FA102
        """Method with py310 union syntax."""
        return param is Undefined

    request = util.get_request("method310")
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is True


def test_union_default() -> None:
    rpc = RPCServer(debug=True)

    @rpc.method()
    def method(  # pyright: ignore[reportUnusedFunction]
        param: Union[int, None, Undefined] = Undefined,
    ) -> bool:
        """Method with union and default undefined."""
        return param is Undefined

    request = util.get_request("method")
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result is True
