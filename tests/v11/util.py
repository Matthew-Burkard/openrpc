"""Methods to make writing unit tests easier."""

from __future__ import annotations

import json
from typing import Any


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
