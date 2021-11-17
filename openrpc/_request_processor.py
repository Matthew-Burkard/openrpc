from typing import Any, Union

from jsonrpcobjects.objects import NotificationType, RequestType


class RequestProcessor:
    def __init__(self, request: Union[RequestType, NotificationType]) -> None:
        self.requests = request

    def execute(self) -> Any:
        pass

    def execute_async(self) -> Any:
        pass
