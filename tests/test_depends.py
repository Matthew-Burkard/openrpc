"""Test depends."""
import json

from openrpc import Depends, RPCServer

rpc = RPCServer(title="Test Depends", version="0.1.0")


@rpc.method
def method_with_dep(arg: int, dep: str = Depends) -> str:
    """Method with dependency to test."""
    return f"{arg}-{dep}"


@rpc.method
async def async_method_with_dep(arg: int, dep: str = Depends) -> None:
    """Method with dependency to test."""
    assert arg == 1
    assert dep == "Coffee"


def test_depends() -> None:
    user = "Coffee"
    req = {"id": 1, "method": "method_with_dep", "params": [1], "jsonrpc": "2.0"}
    result = json.loads(rpc.process_request(json.dumps(req), {"dep": user}))
    assert result["result"] == f"1-{user}"


async def test_depends_async() -> None:
    user = "Coffee"
    req = {
        "id": 1,
        "method": "async_method_with_dep",
        "params": {"arg": 1},
        "jsonrpc": "2.0",
    }
    await rpc.process_request_async(str(req), {"dep": user})
