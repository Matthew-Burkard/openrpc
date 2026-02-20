"""Request context module."""

from __future__ import annotations

from jsonrpcobjects.objects import (
    Notification,
    ParamsNotification,
    ParamsRequest,
    Request,
)
from jsonrpcobjects.parse import ParseResult


class BaseContext:
    """Request context base class."""

    def __init__(
        self,
        scopes: list[str] | None = None,
        raw_request: str | None = None,
        parsed_request: ParseResult | None = None,
    ) -> None:
        """Instantiate a base context object.

        :param scopes: Permissions of this request.
        :param raw_request: Raw request string.
        :param parsed_request: Deserialized request, or parse error.
        """
        self.scopes = scopes or []
        self.raw_request = raw_request
        self.parsed_request = parsed_request


_ = Notification.model_rebuild()
_ = ParamsNotification.model_rebuild()
_ = ParamsRequest.model_rebuild()
_ = Request.model_rebuild()
