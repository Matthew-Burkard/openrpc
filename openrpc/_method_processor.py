"""Provide JSON-RPC2 server class."""
import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Any, Callable, Optional, TypeVar, Union

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

__all__ = ("MethodProcessor",)

T = TypeVar("T", bound=Callable)
log = logging.getLogger("openrpc")
NotificationTypes = (NotificationObject, NotificationObjectParams)
RequestTypes = (RequestObject, RequestObjectParams)
_DEFAULT_ERROR_CODE = -32000


class MethodProcessor:
    """Class to register and execute methods."""

    def __init__(self) -> None:
        """Init a MethodProcessor."""
        self.methods: dict[str, Callable] = {}
        self.uncaught_error_code = _DEFAULT_ERROR_CODE

    def method(self, func: T, method_name: str) -> T:
        """Register a method with this server for later calls."""
        self.methods[method_name] = func
        return func

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        parsed_json = _get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponseObject):
            return parsed_json.json()

        # Batch
        if isinstance(parsed_json, list):
            requests = [_get_request_object(it) for it in parsed_json]
            results: list[str] = []
            for req in requests:
                if isinstance(req, ErrorResponseObject):
                    results.append(req.json())
                    continue
                if req.method not in self.methods:
                    if isinstance(req, (RequestObject, RequestObjectParams)):
                        results.append(_get_method_not_found_error(req))
                    continue

                fun = self.methods[req.method]
                resp = RequestProcessor(fun, self.uncaught_error_code, req).execute()
                # If resp is None, request is a notification.
                if resp is not None:
                    results.append(resp)
            return f"[{','.join(results)}]"

        # Single Request
        request = _get_request_object(parsed_json)
        if isinstance(request, ErrorResponseObject):
            return request.json()
        if request.method not in self.methods:
            if isinstance(request, (RequestObject, RequestObjectParams)):
                return _get_method_not_found_error(request)
            return None
        result = RequestProcessor(
            self.methods[request.method], self.uncaught_error_code, request
        ).execute()
        return None if isinstance(request, NotificationTypes) else result

    async def process_async(self, data: Union[bytes, str]) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :return: A valid JSON-RPC2 response.
        """
        parsed_json = _get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponseObject):
            return parsed_json.json()

        # Batch
        if isinstance(parsed_json, list):

            async def _process_request(
                request: Union[ErrorResponseObject, NotificationType, RequestType]
            ) -> Any:
                if isinstance(request, ErrorResponseObject):
                    return request.json()
                if request.method not in self.methods:
                    if isinstance(request, (RequestObject, RequestObjectParams)):
                        return _get_method_not_found_error(request)
                    return None

                fun = self.methods[request.method]
                if isinstance(request, RequestTypes):
                    return await RequestProcessor(
                        fun, self.uncaught_error_code, request
                    ).execute_async()
                # To get here, request must be a notification.
                await RequestProcessor(
                    fun, self.uncaught_error_code, request
                ).execute_async()

            results = await asyncio.gather(
                *[_process_request(_get_request_object(it)) for it in parsed_json]
            )
            return f"[{','.join(str(r) for r in results if r is not None)}]"

        # Single Request
        req = _get_request_object(parsed_json)
        if isinstance(req, ErrorResponseObject):
            return req.json()
        if req.method not in self.methods:
            if isinstance(req, (RequestObject, RequestObjectParams)):
                return _get_method_not_found_error(req)
            return None
        result = await RequestProcessor(
            self.methods[req.method], self.uncaught_error_code, req
        ).execute_async()
        return None if isinstance(req, NotificationTypes) else result


def _get_method_not_found_error(req: Union[NotificationType, RequestType]) -> str:
    return ErrorResponseObject(
        id=None if isinstance(req, NotificationTypes) else req.id,
        error=ErrorObjectData(**{**METHOD_NOT_FOUND.dict(), **{"data": req.method}}),
    ).json()


def _get_parsed_json(data: Union[bytes, str]) -> Union[ErrorResponseObject, dict, list]:
    try:
        parsed_json = json.loads(data)
    except (TypeError, JSONDecodeError) as error:
        log.exception("%s:", type(error).__name__)
        return ErrorResponseObject(error=PARSE_ERROR)
    return parsed_json


def _get_request_object(
    data: Any,
) -> Union[ErrorResponseObject, NotificationType, RequestType]:
    try:
        is_request = data.get("id") is not None
        has_params = data.get("params") is not None
        if is_request:
            return RequestObjectParams(**data) if has_params else RequestObject(**data)
        return (
            NotificationObjectParams(**data)
            if has_params
            else NotificationObject(**data)
        )
    except (TypeError, ValidationError) as error:
        log.exception("%s:", type(error).__name__)
        return ErrorResponseObject(
            id=data.get("id"),
            error=ErrorObjectData(**{**INVALID_REQUEST.dict(), **{"data": data}}),
        )
    except AttributeError:
        return ErrorResponseObject(
            error=ErrorObjectData(**{**INVALID_REQUEST.dict(), **{"data": data}})
        )
