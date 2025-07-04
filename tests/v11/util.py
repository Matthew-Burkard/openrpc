"""Methods to make writing unit tests easier."""

from __future__ import annotations

import json
from typing import Any, Callable

from openrpc.app import RPCApp
from openrpc.context import Context


def req_str(method: str, params: dict[str, Any] | list[Any] | None = None) -> str:
    if params:
        p = json.dumps(params)
        return f'{{"id":0,"method":"{method}","params":{p},"jsonrpc":"2.0"}}'
    return f'{{"id":0,"method":"{method}","jsonrpc":"2.0"}}'


def notify_str(method: str, params: dict[str, Any] | list[Any] | None = None) -> str:
    if params:
        p = json.dumps(params)
        return f'{{"method":"{method}","params":{p},"jsonrpc":"2.0"}}'
    return f'{{"method":"{method}","jsonrpc":"2.0"}}'


async def get_result(
    app: RPCApp,
    method: Callable[[Any], Any],
    params: list[Any] | dict[str, Any],
    context: Context | None = None,
) -> Any:
    request = req_str(method.__name__, params)
    response = await app.process(request, context=context or Context())
    data = json.loads(response or "")
    if "result" in data:
        return data["result"]
    return data
