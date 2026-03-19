"""Test use of Pydantic aliases."""

import json

import pytest
from pydantic import BaseModel, Field

from openrpc import BaseContext, RPCApp
from tests.v11 import util


class Model(BaseModel):
    pizza: str = Field(alias="calories")


@pytest.mark.asyncio
async def test_alias() -> None:
    rpc = RPCApp(debug=True)

    @rpc.method()
    async def method(type_: str) -> Model:  # pyright: ignore[reportUnusedFunction]
        """Test method."""
        return Model(calories=type_)

    request = util.req_str("method", {"type_": "philly cheese steak"})
    response = json.loads(await rpc.process(request, BaseContext()) or "")
    assert response["result"]["calories"] == "philly cheese steak"
