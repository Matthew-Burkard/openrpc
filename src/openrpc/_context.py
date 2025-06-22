"""Request context module."""

from jsonrpcobjects.parse import ParseResult
from pydantic import BaseModel


class ContextBase(BaseModel):
    """Request context base class.

    Request context will optionally be passed to any method.
    It will carry RPC request data as well as any other properties suppllied by the
    context factory.
    """

    scopes: list[str] = []
    """Permissions of this request."""

    def __init__(self) -> None:
        self.request: str
        self.parsed_request: ParseResult
