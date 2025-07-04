"""Test use of Pydantic aliases."""

import json

import pytest
from pydantic import BaseModel, Field

from openrpc.app import RPCApp
from openrpc.context import Context
from tests.v11 import util


class Model(BaseModel):
    pizza: str = Field(..., alias="calories")  # type: ignore


@pytest.mark.asyncio
async def test_alias() -> None:
    rpc = RPCApp(debug=True)

    @rpc.method()
    async def method(type_: str) -> Model:  # type: ignore
        """Test method."""
        return Model(calories=type_)

    request = util.req_str("method", {"type_": "philly cheese steak"})
    response = json.loads(await rpc.process(request, Context()) or "")
    assert response["result"]["calories"] == "philly cheese steak"
