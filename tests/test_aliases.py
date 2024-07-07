"""Test use of Pydantic aliases."""

import pytest
from pydantic import BaseModel, Field

from openrpc import RPCServer
from tests import util


class TestModel(BaseModel):
    pizza: str = Field(..., alias="calories")


@pytest.mark.asyncio
async def test_alias() -> None:
    rpc = RPCServer()

    @rpc.method()
    def method(type_: str) -> TestModel:
        """Test method."""
        return TestModel(calories=type_)

    request = util.get_request("method", '{"type_": "philly cheese steak"}')
    response = util.parse_result_response(rpc.process_request(request))
    assert response.result["calories"] == "philly cheese steak"

    request = util.get_request("method", '{"type_": "spinach and onion"}')
    response = util.parse_result_response(await rpc.process_request_async(request))
    assert response.result["calories"] == "spinach and onion"
