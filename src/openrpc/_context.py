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


class ContextBase(BaseModel):
    """Request context base class.

    Request context will optionally be passed to any method.
    It will carry RPC request data as well as any other properties suppllied by the
    context factory.
    """

    scopes: list[str] = []
    """Permissions of this request."""

    request: Union[str, None] = None
    """Raw request string."""

    parsed_request: Union[ParseResult, None] = None
    """Deserialized request, or parse error."""


ContextBase.model_rebuild()
Notification.model_rebuild()
ParamsNotification.model_rebuild()
ParamsRequest.model_rebuild()
Request.model_rebuild()
