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
from pydantic import ValidationError

from openrpc._request_processor import RequestProcessor
from openrpc.objects import MethodObject

__all__ = ("RPCServer",)

T = Type[Callable]
log = logging.getLogger("openrpc")
NotificationTypes = (NotificationObject, NotificationObjectParams)
RequestTypes = (RequestObject, RequestObjectParams)


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
                if it.method not in self.methods.keys():
                    results.append(get_method_not_found_error(it))

                fun = self.methods[it.method].fun
                if isinstance(it, ErrorResponseObject):
                    results.append(it.json())
                elif isinstance(it, RequestTypes):
                    results.append(
                        RequestProcessor(fun, self.uncaught_error_code, it).execute()
                    )
                else:
                    RequestProcessor(fun, self.uncaught_error_code, it).execute()
            return f"[{','.join(results)}]"

        # Single Request
        req = get_request_object(parsed_json)
        if isinstance(req, ErrorResponseObject):
            return req.json()
        if req.method not in self.methods.keys():
            return get_method_not_found_error(req)
        result = RequestProcessor(
            self.methods[req.method].fun, self.uncaught_error_code, req
        ).execute()
        return None if isinstance(req, NotificationTypes) else result

    async def process_async(self, data: Union[bytes, str]) -> Optional[str]:
        parsed_json = get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponseObject):
            return parsed_json.json()

        # Batch
        if isinstance(parsed_json, list):

            async def one_iter(it) -> Any:
                if it.method not in self.methods.keys():
                    return get_method_not_found_error(it)

                fun = self.methods[it.method].fun
                if isinstance(it, ErrorResponseObject):
                    return it.json()
                elif isinstance(it, RequestTypes):
                    return await RequestProcessor(
                        fun, self.uncaught_error_code, it
                    ).execute_async()
                await RequestProcessor(
                    fun, self.uncaught_error_code, it
                ).execute_async()

            results = await asyncio.gather(
                *[one_iter(get_request_object(it)) for it in parsed_json]
            )
            return f"[{','.join(str(r) for r in results if r is not None)}]"

        # Single Request
        req = get_request_object(parsed_json)
        if isinstance(req, ErrorResponseObject):
            return req.json()
        if req.method not in self.methods.keys():
            return get_method_not_found_error(req)
        result = await RequestProcessor(
            self.methods[req.method].fun, self.uncaught_error_code, req
        ).execute_async()
        return None if isinstance(req, NotificationTypes) else result


def get_method_not_found_error(req: Union[NotificationType, RequestType]) -> str:
    return ErrorResponseObject(
        id=None if isinstance(req, NotificationTypes) else req.id,
        error=ErrorObjectData(
            **{**METHOD_NOT_FOUND.dict(), **{"data": req.method}}
        ),
    ).json()


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
) -> Union[ErrorResponseObject, NotificationType, RequestType]:
    is_request = data.get("id") is not None
    has_params = data.get("params") is not None

    try:
        if is_request:
            return (RequestObjectParams if has_params else RequestObject)(**data)
        return (NotificationObjectParams if has_params else NotificationObject)(**data)
    except (TypeError, ValidationError) as e:
        log.exception(f"{type(e).__name__}:")
        return ErrorResponseObject(
            id=data.get("id"),
            error=ErrorObjectData(**{**INVALID_REQUEST.dict(), **{"data": data}}),
        )
