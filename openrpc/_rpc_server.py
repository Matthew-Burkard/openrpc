import asyncio
import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Callable, Optional, Type, Union

from jsonrpcobjects.errors import INVALID_REQUEST, METHOD_NOT_FOUND, PARSE_ERROR
from jsonrpcobjects.objects import (
    ErrorObjectData,
    ErrorResponseObject,
    NotificationObject,
    NotificationObjectParams,
    NotificationType,
    RequestObject,
    RequestObjectParams,
    RequestType,
)

from openrpc._request_processor import RequestProcessor
from openrpc.objects import MethodObject

__all__ = ("RPCServer",)

T = Type[Callable]
log = logging.getLogger("openrpc")


@dataclass
class RegisteredMethod:
    fun: Callable
    method: MethodObject


class RPCServer:
    def __init__(self, server_error_code: int) -> None:
        self.methods: dict[str, RegisteredMethod] = {}
        self.uncaught_error_code: Optional[int] = server_error_code

    def method(self, func: T, method: MethodObject) -> T:
        log.debug("Registering method [%s]", func.__name__)
        method.name = method.name or func.__name__
        self.methods[method.name] = RegisteredMethod(func, method)
        return func

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        parsed_json = get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponseObject):
            return parsed_json.json()

        # Batch
        if isinstance(parsed_json, list):
            requests = [get_request_object(it) for it in parsed_json]
            results = []
            for it in requests:
                if isinstance(it, ErrorResponseObject):
                    results.append(it.json())
                elif it.method not in self.methods.keys():
                    results.append(
                        ErrorResponseObject(
                            id=None if isinstance(it, NotificationType) else it.id,
                            error=ErrorObjectData(
                                **{**METHOD_NOT_FOUND.dict(), **{"data": it.method}}
                            ),
                        ).json()
                    )
                elif isinstance(it, RequestType):
                    results.append(RequestProcessor(it).execute())
                else:
                    RequestProcessor(it).execute()
            return f"[{','.join(results)}]"

        # Single Request
        # noinspection DuplicatedCode
        req = get_request_object(parsed_json)
        if isinstance(req, ErrorResponseObject):
            return req.json()
        if req.method not in self.methods.keys():
            return ErrorResponseObject(
                id=None if isinstance(req, NotificationType) else req.id,
                error=ErrorObjectData(
                    **{**METHOD_NOT_FOUND.dict(), **{"data": req.method}}
                ),
            ).json()
        result = RequestProcessor(req).execute()
        return None if isinstance(req, NotificationType) else result

    async def process_async(self, data: Union[bytes, str]) -> Optional[str]:
        parsed_json = get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponseObject):
            return parsed_json.json()

        # Batch
        if isinstance(parsed_json, list):

            async def one_iter(it) -> Any:
                if isinstance(it, ErrorResponseObject):
                    return it.json()
                elif it.method not in self.methods.keys():
                    return ErrorResponseObject(
                        id=None if isinstance(it, NotificationType) else it.id,
                        error=ErrorObjectData(
                            **{**METHOD_NOT_FOUND.dict(), **{"data": it.method}}
                        ),
                    ).json()
                elif isinstance(it, RequestType):
                    return await RequestProcessor(it).execute_async()
                await RequestProcessor(it).execute_async()

            results = await asyncio.gather(
                one_iter(get_request_object(it)) for it in parsed_json
            )
            return f"[{','.join(results)}]"

        # Single Request
        # noinspection DuplicatedCode
        req = get_request_object(parsed_json)
        if isinstance(req, ErrorResponseObject):
            return req.json()
        if req.method not in self.methods.keys():
            return ErrorResponseObject(
                id=None if isinstance(req, NotificationType) else req.id,
                error=ErrorObjectData(
                    **{**METHOD_NOT_FOUND.dict(), **{"data": req.method}}
                ),
            ).json()
        result = await RequestProcessor(req).execute_async()
        return None if isinstance(req, NotificationType) else result


def get_parsed_json(data: Union[bytes, str]) -> Union[ErrorResponseObject, dict, list]:
    try:
        parsed_json = json.loads(data)
    except (TypeError, JSONDecodeError) as e:
        log.exception(f"{type(e).__name__}:")
        return ErrorResponseObject(error=PARSE_ERROR)

    if not isinstance(parsed_json, (list, dict)):
        log.error("Invalid request [%s]", parsed_json)
        return ErrorResponseObject(
            error=ErrorObjectData(**{**INVALID_REQUEST.dict(), **{"data": parsed_json}})
        )
    return parsed_json


def get_request_object(
    data: dict[str, Any]
) -> Union[RequestType, NotificationType, ErrorResponseObject]:
    is_request = data.get("id") is not None
    has_params = data.get("params") is not None

    try:
        if is_request:
            return (RequestObjectParams if has_params else RequestObject)(**data)
        return (NotificationObjectParams if has_params else NotificationObject)(**data)
    except TypeError as e:
        log.exception(f"{type(e).__name__}:")
        return ErrorResponseObject(
            id=data.get("id"),
            error=ErrorObjectData(**{**INVALID_REQUEST.dict(), **{"data": data}}),
        )
