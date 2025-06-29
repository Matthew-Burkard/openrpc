"""Methods to make writing unit tests easier."""

from __future__ import annotations

import json
from typing import Any


def req_str(method: str, params: dict[str, Any] | list[Any]) -> str:
    p = json.dumps(params)
    return f'{{"id":0,"method":{method},"params":{p},"jsonrpc":"2.0"}}'
