"""Test deserializing union types."""

from typing import Union

import pytest
from pydantic import BaseModel, StrictInt, StrictStr

from tests.v11 import util


class CustomA(BaseModel):
    int_field: StrictInt


class CustomB(BaseModel):
    str_field: StrictStr


def func(c: Union[CustomA, CustomB]) -> bool:
    """Test function."""
    return isinstance(
        c, (CustomA, CustomB)
    )  # pyright: ignore[reportUnnecessaryIsInstance]


@pytest.mark.asyncio
async def test_union_casting() -> None:
    rpc = util.get_app_with_method(func)
    result = await util.get_result(rpc, func, [{"int_field": 1}])
    assert result is True
    result = await util.get_result(rpc, func, [{"str_field": "coffee"}])
    assert result is True
    result = await util.get_result(rpc, func, [{"int_field": 3.14}])
    assert result["error"]["message"] == "Invalid params"
