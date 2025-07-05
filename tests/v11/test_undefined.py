"""Tests for `Undefined` type."""

import sys
from typing import Optional, Union

import pytest

from openrpc import Undefined
from tests.v11 import util


@pytest.mark.asyncio
async def test_undefined() -> None:
    def method(param: str = Undefined) -> bool:  # type: ignore
        """Method with non-required param."""
        return param is Undefined

    rpc = util.get_app_with_method(method)
    result = await util.get_result(rpc, method)
    assert result is True
    result = await util.get_result(rpc, method, {"param": ""})
    assert result is False
    result = await util.get_result(rpc, method, [""])
    assert result is False


@pytest.mark.asyncio
async def test_undefined_type() -> None:
    def undefined_type(param: Union[Undefined, str]) -> bool:  # type: ignore
        """Method using undefined as a parameter type."""
        return param is Undefined

    rpc = util.get_app_with_method(undefined_type)
    result = await util.get_result(rpc, undefined_type)
    assert result is True
    result = await util.get_result(rpc, undefined_type, {"param": ""})
    assert result is False
    result = await util.get_result(rpc, undefined_type, [""])
    assert result is False


@pytest.mark.asyncio
async def test_undefined_with_required() -> None:
    def method(req: str, param: Optional[Union[str, Undefined]] = Undefined) -> bool:
        """Method with required and non-required params."""
        assert isinstance(req, str)
        return param is Undefined

    rpc = util.get_app_with_method(method)
    result = await util.get_result(rpc, method, [""])
    assert result is True


def test_undefined_discover() -> None:
    def method(param: str = Undefined) -> bool:  # type: ignore  # noqa: ARG001
        """Method with non-required param."""
        assert param is Undefined

    rpc = util.get_app_with_method(method)
    schema_param = rpc.discover()["methods"][0]["params"][0]
    assert schema_param["required"] is False
    assert "default" not in schema_param["schema"]


@pytest.mark.asyncio
async def test_310_union() -> None:
    if sys.version_info < (3, 10):
        return

    def method310(param: int | None | Undefined) -> bool:  # type: ignore
        """Method with py310 union syntax."""
        return param is Undefined

    rpc = util.get_app_with_method(method310)
    result = await util.get_result(rpc, method310)
    assert result is True


@pytest.mark.asyncio
async def test_union_default() -> None:
    def method(param: Union[int, None, Undefined] = Undefined) -> bool:  # type: ignore
        """Method with union and default undefined."""
        return param is Undefined

    rpc = util.get_app_with_method(method)
    result = await util.get_result(rpc, method)
    assert result is True
