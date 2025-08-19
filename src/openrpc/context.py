"""Request context module."""

from typing import Union

from jsonrpcobjects.objects import (
    Notification,
    ParamsNotification,
    ParamsRequest,
    Request,
)
from jsonrpcobjects.parse import ParseResult
from pydantic import BaseModel


class BaseContext(BaseModel):
    """Request context base class."""

    scopes: list[str] = []
    """Permissions of this request."""

    raw_request: Union[str, None] = None
    """Raw request string."""

    parsed_request: Union[ParseResult, None] = None
    """Deserialized request, or parse error."""


BaseContext.model_rebuild()
Notification.model_rebuild()
ParamsNotification.model_rebuild()
ParamsRequest.model_rebuild()
Request.model_rebuild()
