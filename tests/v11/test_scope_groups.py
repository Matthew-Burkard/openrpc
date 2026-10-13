"""Test OR-group scope requirements."""

import pytest

from openrpc import BaseContext, Info, RPCApp, RPCPermissionError, Scope
from tests.v11 import util

rpc = RPCApp(Info(title="Test Scope Groups", version="0.1.0"))


admin = Scope(name="admin")
capability_read = Scope(name="capability:read")
service = Scope(name="service")


@rpc.method(scopes=[admin, capability_read])
def legacy_and(arg: int) -> int:
    """Legacy AND method: requires all listed scopes."""
    return arg


@rpc.method(
    scope_groups=[
        [admin, capability_read],
        [service],
    ]
)
def or_groups(arg: int) -> int:
    """OR-group method: satisfied by ANY single group."""
    return arg


@rpc.method(
    scopes=[admin],
    scope_groups=[[service]],
)
def combined(arg: int) -> int:
    """Combined: legacy `scopes` treated as an additional group."""
    return arg


@pytest.mark.asyncio
async def test_legacy_and_pass() -> None:
    context = BaseContext(scopes=[admin.name, capability_read.name])
    result = await util.get_result(rpc, legacy_and, [1], context)
    assert result == 1


@pytest.mark.asyncio
async def test_legacy_and_fail() -> None:
    context = BaseContext(scopes=[admin.name])
    result = await util.get_result(rpc, legacy_and, [1], context)
    assert result["error"]["message"] == "Permission error"


@pytest.mark.asyncio
async def test_or_groups_pass_first_group() -> None:
    context = BaseContext(scopes=[admin.name, capability_read.name])
    result = await util.get_result(rpc, or_groups, [1], context)
    assert result == 1


@pytest.mark.asyncio
async def test_or_groups_pass_second_group() -> None:
    context = BaseContext(scopes=[service.name])
    result = await util.get_result(rpc, or_groups, [1], context)
    assert result == 1


@pytest.mark.asyncio
async def test_or_groups_fail_partial_group() -> None:
    # Holds only part of group 1 and none of group 2.
    context = BaseContext(scopes=[admin.name])
    result = await util.get_result(rpc, or_groups, [1], context)
    assert result["error"]["message"] == "Permission error"


@pytest.mark.asyncio
async def test_or_groups_fail_no_scopes() -> None:
    context = BaseContext()
    result = await util.get_result(rpc, or_groups, [1], context)
    assert result["error"]["message"] == "Permission error"


@pytest.mark.asyncio
async def test_combined_scopes_and_groups() -> None:
    # Satisfied by legacy `scopes` group.
    context = BaseContext(scopes=[admin.name])
    assert await util.get_result(rpc, combined, [1], context) == 1
    # Satisfied by `scope_groups` group.
    context = BaseContext(scopes=[service.name])
    assert await util.get_result(rpc, combined, [1], context) == 1
    # Satisfied by neither.
    context = BaseContext(scopes=[capability_read.name])
    result = await util.get_result(rpc, combined, [1], context)
    assert result["error"]["message"] == "Permission error"


def test_scoped_or_groups_pass() -> None:
    method = rpc.scoped(or_groups, [service.name])
    assert method(1) == 1


def test_scoped_or_groups_fail() -> None:
    method = rpc.scoped(or_groups, [admin.name])
    with pytest.raises(RPCPermissionError):
        _ = method(1)


def test_scope_groups_discover() -> None:
    doc = rpc.openrpc()
    methods = {method.name: method for method in doc.methods}
    # Regular method keeps flat `x-scopes` and gets normalized `x-scope-groups`.
    assert methods["legacy_and"].x_scopes == [admin, capability_read]
    assert methods["legacy_and"].x_scope_groups == [[admin, capability_read]]
    # OR-group method serializes its groups.
    assert methods["or_groups"].x_scopes == []
    assert methods["or_groups"].x_scope_groups == [
        [admin, capability_read],
        [service],
    ]
