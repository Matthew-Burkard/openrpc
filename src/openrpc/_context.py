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


_ = BaseContext.model_rebuild()
_ = Notification.model_rebuild()
_ = ParamsNotification.model_rebuild()
_ = ParamsRequest.model_rebuild()
_ = Request.model_rebuild()
