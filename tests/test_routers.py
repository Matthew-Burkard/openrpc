"""Unit tests for RPC method routers."""
import json

from jsonrpcobjects.objects import Request

from openrpc import RPCRouter, RPCServer

rpc = RPCServer(title="RouterTestServer", version="1.0.0")
auth_router = RPCRouter()


@auth_router.method
def method_added_before_router_included() -> None:
    """Do nothing."""


rpc.include_router(auth_router, prefix="auth.")


@auth_router.method
def login() -> str:
    """Test auth method signature."""
    return "AUTH_TOKEN_HERE"


def test_router_method_call() -> None:
    req = Request(id=1, method="auth.login")
    resp = json.loads(rpc.process_request(req.model_dump_json()))
    assert resp["result"] == "AUTH_TOKEN_HERE"


def test_router_remove() -> None:
    auth_router.remove("login")
    req = Request(id=1, method="auth.login")
    resp = json.loads(rpc.process_request(req.model_dump_json()))
    assert resp["error"]["code"] == -32601  # Method not found code.


router_with_tags_no_prefix = RPCRouter()
rpc.include_router(router_with_tags_no_prefix, tags=["test_tag"])


@router_with_tags_no_prefix.method
def return_coffee() -> str:
    """Return "Coffee"."""
    return "Coffee"


@router_with_tags_no_prefix.method(tags=["does_nothing"])
def do_nothing() -> str:
    """Do nothing."""


def test_tags_no_prefix_router_method_call() -> None:
    req = Request(id=1, method="return_coffee")
    resp = json.loads(rpc.process_request(req.model_dump_json()))
    assert resp["result"] == "Coffee"


def test_tags() -> None:
    tags = [m for m in rpc.methods if m.name == "do_nothing"][0].tags
    assert [t.name for t in tags] == ["does_nothing", "test_tag"]


def test_tags_no_prefix_router_remove() -> None:
    router_with_tags_no_prefix.remove("return_coffee")
    req = Request(id=1, method="return_coffee")
    resp = json.loads(rpc.process_request(req.model_dump_json()))
    assert resp["error"]["code"] == -32601  # Method not found code.


def test_debug() -> None:
    rpc.include_router(auth_router, prefix="auth.")
    rpc.debug = True
    for router in rpc._routers:
        assert router.debug is True
    rpc.debug = False
    for router in rpc._routers:
        assert router.debug is False
