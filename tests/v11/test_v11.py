"""Test API hooks."""

from __future__ import annotations

import pytest
from jsonrpcobjects.parse import ParseResult

from openrpc import Info
from openrpc._app import RPCApp
from openrpc._context import ContextBase

OAUTH2 = "OAUTH2"


class Scope:
    """OAUTH2 security scope."""

    READ_SUSHI = "read_sushi"
    WRITE_COFFEE = "write_coffee"


class Context(ContextBase):
    """Request context."""


class ConnectionRPCServer(RPCApp):
    """RPC server that provides a database connection."""

    def __init__(self, config: Info | None = None, *, debug: bool = False) -> None:
        """Instantiate RPC server with database connection."""
        super().__init__(config, debug=debug)

    async def handle_request(
        self, parse_result: ParseResult, context: ContextBase
    ) -> str | None:
        """Handle a JSON-RPC request.

        :param parse_result: Parsed JSON-RPC request.
        :param context: Context data regarding the request.
        :return: JSON-RPC response string or null if request was a notification.
        """
        print("Pre call hook")
        result = await super().handle_request(parse_result, context)
        print("Post call hook")
        return result


rpc = ConnectionRPCServer()


@rpc.method(security={OAUTH2: [Scope.READ_SUSHI, Scope.WRITE_COFFEE]})
async def spinach(context: Context, a: int, b: int) -> int:
    """Add two integers."""
    await broccoli(context, a, b)
    return a + b


@rpc.method()
async def broccoli(context: Context, a: int, b: int) -> int:
    """Subtract two integers."""
    print(context)
    return a - b


@rpc.method()
async def kale(a: int, b: int) -> int:
    """Addd two integers."""
    return a + b


@pytest.mark.asyncio
async def test_method_call() -> None:
    result: int = await rpc.call_method(kale.__name__, [1, 0], Context())
    assert result == 1


@pytest.mark.asyncio
async def test_context_injection() -> None:
    result: int = await rpc.call_method(broccoli.__name__, [1, 0], Context())
    assert result == 1
