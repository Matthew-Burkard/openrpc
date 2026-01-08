"""OpenRPC base error class."""

from __future__ import annotations

from typing import Any


class OpenRPCError(Exception):
    """Base error for OpenRPC API."""

    def __init__(
        self, code: int, msg: str, data: Any | None = None, *args: object
    ) -> None:
        """Instantiate OpenRPC error."""
        self.code = code
        self.message = msg
        self.data = data
        super().__init__(*args)
