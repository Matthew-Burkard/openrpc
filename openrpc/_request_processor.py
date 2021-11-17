import logging
from typing import Any, Callable, Union

from jsonrpcobjects.objects import NotificationType, RequestType

__all__ = ("RequestProcessor",)

log = logging.getLogger("openrpc")


class RequestProcessor:
    def __init__(
        self, method: Callable, request: Union[RequestType, NotificationType]
    ) -> None:
        self.method = method
        self.requests = request

    def execute(self) -> Any:
        pass

    def execute_async(self) -> Any:
        pass
