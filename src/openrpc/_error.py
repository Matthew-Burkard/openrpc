"""OpenRPC base error class."""

from __future__ import annotations

from typing import Any


class OpenRPCError(Exception):
    """Base error for OpenRPC API."""

    def __init__(
        self, code: int, message: str, data: Any | None = None, *args: object
    ) -> None:
        """Instantiate OpenRPC error.

        :param code: A Number that indicates the error type that occurred.
        :param message: A short description of the error.
        :param data: Value that contains additional information about the error.
        :param args: Python `Exeption` arguments.
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(*args)
