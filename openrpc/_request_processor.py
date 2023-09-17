"""Module responsible for parsing JSON RPC 2.0 requests."""

__all__ = ("RequestProcessor",)

import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Any, Optional, Union

from jsonrpcobjects.errors import INVALID_REQUEST, METHOD_NOT_FOUND, PARSE_ERROR
from jsonrpcobjects.objects import (
    DataError,
    ErrorResponse,
    Notification,
    NotificationType,
    ParamsNotification,
    ParamsRequest,
    Request,
    RequestType,
)
from pydantic import ValidationError

from openrpc._common import RPCMethod
from openrpc._method_processor import MethodProcessor

log = logging.getLogger("openrpc")
NotificationTypes = (Notification, ParamsNotification)
RequestTypes = (Request, ParamsRequest)
_DEFAULT_ERROR_CODE = -32000


class RequestProcessor:
    """Class to parse requests and pass results to MethodProcessor."""

    def __init__(self, *, debug: bool) -> None:
        """Init a RequestProcessor.

        :param debug: Include internal error details in responses.
        """
        self.debug = debug
        self.methods: dict[str, RPCMethod] = {}
        self.uncaught_error_code = _DEFAULT_ERROR_CODE

    def method(self, function: RPCMethod, method_name: str) -> None:
        """Register a method with this server for later calls.

        :param function: Function to call for this method.
        :param method_name: Name of the RPC method.
        :return: None.
        """
        self.methods[method_name] = function

    def process(
        self,
        data: Union[bytes, str],
        depends: Optional[dict[str, Any]],
        security: Optional[dict[str, list[str]]],
    ) -> Optional[str]:
        """Parse a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :param depends: Values passed to functions with dependencies.
        :param security: Scheme and scopes of method caller.
        :return: A valid JSON-RPC2 response.
        """
        parsed_json = _get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponse):
            return parsed_json.model_dump_json()

        # Batch
        if isinstance(parsed_json, list):
            requests = [_get_request_object(it) for it in parsed_json]
            results: list[str] = []
            for req in requests:
                if isinstance(req, ErrorResponse):
                    results.append(req.model_dump_json())
                    continue
                if req.method not in self.methods:
                    if isinstance(req, (Request, ParamsRequest)):
                        results.append(_get_method_not_found_error(req))
                    continue

                resp = MethodProcessor(
                    self.methods[req.method],
                    self.uncaught_error_code,
                    req,
                    depends,
                    security,
                    debug=self.debug,
                ).execute()
                # If resp is None, request is a notification.
                if resp is not None:
                    results.append(resp)
            return f"[{','.join(results)}]"

        # Single Request
        request = _get_request_object(parsed_json)
        if isinstance(request, ErrorResponse):
            return request.model_dump_json()
        if request.method not in self.methods:
            if isinstance(request, (Request, ParamsRequest)):
                return _get_method_not_found_error(request)
            return None
        result = MethodProcessor(
            self.methods[request.method],
            self.uncaught_error_code,
            request,
            depends,
            security,
            debug=self.debug,
        ).execute()
        return None if isinstance(request, NotificationTypes) else result

    async def process_async(
        self,
        data: Union[bytes, str],
        depends: Optional[dict[str, Any]],
        security: Optional[dict[str, list[str]]],
    ) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :param depends: Values passed to functions with dependencies.
        :param security: Scheme and scopes of method caller.
        :return: A valid JSON-RPC2 response.
        """
        parsed_json = _get_parsed_json(data)
        if isinstance(parsed_json, ErrorResponse):
            return parsed_json.model_dump_json()

        # Batch
        if isinstance(parsed_json, list):

            async def _process_request(
                request: Union[ErrorResponse, NotificationType, RequestType]
            ) -> Any:
                if isinstance(request, ErrorResponse):
                    return request.model_dump_json()
                if request.method not in self.methods:
                    if isinstance(request, (Request, ParamsRequest)):
                        return _get_method_not_found_error(request)
                    return None

                method = self.methods[request.method]
                method_result = await MethodProcessor(
                    method,
                    self.uncaught_error_code,
                    request,
                    depends,
                    security,
                    debug=self.debug,
                ).execute_async()
                if isinstance(request, RequestTypes):
                    return method_result
                return None

            results = await asyncio.gather(
                *[_process_request(_get_request_object(it)) for it in parsed_json]
            )
            return f"[{','.join(str(r) for r in results if r is not None)}]"

        # Single Request
        req = _get_request_object(parsed_json)
        if isinstance(req, ErrorResponse):
            return req.model_dump_json()
        if req.method not in self.methods:
            if isinstance(req, (Request, ParamsRequest)):
                return _get_method_not_found_error(req)
            return None
        result = await MethodProcessor(
            self.methods[req.method],
            self.uncaught_error_code,
            req,
            depends,
            security,
            debug=self.debug,
        ).execute_async()

        return None if isinstance(req, NotificationTypes) else result


def _get_method_not_found_error(req: Union[NotificationType, RequestType]) -> str:
    return ErrorResponse(
        id=None if isinstance(req, NotificationTypes) else req.id,
        error=DataError(**{**METHOD_NOT_FOUND.model_dump(), **{"data": req.method}}),
    ).model_dump_json()


def _get_parsed_json(data: Union[bytes, str]) -> Union[ErrorResponse, dict, list]:
    try:
        parsed_json = json.loads(data)
    except (TypeError, JSONDecodeError) as error:
        log.exception("%s:", type(error).__name__)
        return ErrorResponse(id=None, error=PARSE_ERROR)
    return parsed_json


def _get_request_object(
    data: Any,
) -> Union[ErrorResponse, NotificationType, RequestType]:
    try:
        is_request = data.get("id") is not None
        has_params = data.get("params") is not None
        if is_request:
            return ParamsRequest(**data) if has_params else Request(**data)
        return ParamsNotification(**data) if has_params else Notification(**data)
    except (TypeError, ValidationError) as error:
        log.exception("%s:", type(error).__name__)
        return ErrorResponse(
            id=data.get("id"),
            error=DataError(**{**INVALID_REQUEST.model_dump(), **{"data": data}}),
        )
    except AttributeError:
        return ErrorResponse(
            id=None,
            error=DataError(**{**INVALID_REQUEST.model_dump(), **{"data": data}}),
        )
