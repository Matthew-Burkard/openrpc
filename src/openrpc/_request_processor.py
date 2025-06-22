"""Module responsible for parsing JSON RPC 2.0 requests."""

__all__ = ("RequestProcessor",)

import asyncio
import logging
from typing import Any, Optional, Union

from jsonrpcobjects.errors import METHOD_NOT_FOUND
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
from jsonrpcobjects.parse import parse_request

from openrpc._common import RPCMethod, SecurityFunctionDetails
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
        caller_details: Optional[Any],
        security: Optional[SecurityFunctionDetails],
    ) -> Optional[str]:
        """Parse a JSON-RPC2 request and get the response.

        :param data: A JSON-RPC2 request.
        :param caller_details: Values passed to functions with
            dependencies and security schemes.
        :param security: Server security function details.
        :return: A valid JSON-RPC2 response.
        """
        parsed_request = parse_request(data, debug=self.debug)
        if isinstance(parsed_request, ErrorResponse):
            return parsed_request.model_dump_json()

        # Batch
        if isinstance(parsed_request, list):
            results: list[str] = []
            for req in parsed_request:
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
                    caller_details,
                    security,
                    debug=self.debug,
                ).execute()
                # If resp is None, request is a notification.
                if resp is not None:
                    results.append(resp)
            return f"[{','.join(results)}]"

        # Single Request
        if parsed_request.method not in self.methods:
            if isinstance(parsed_request, (Request, ParamsRequest)):
                return _get_method_not_found_error(parsed_request)
            return None
        result = MethodProcessor(
            self.methods[parsed_request.method],
            self.uncaught_error_code,
            parsed_request,
            caller_details,
            security,
            debug=self.debug,
        ).execute()
        return None if isinstance(parsed_request, NotificationTypes) else result

    async def process_async(
        self,
        data: Union[bytes, str],
        caller_details: Optional[Any],
        security: Optional[SecurityFunctionDetails],
    ) -> Optional[str]:
        """Process a JSON-RPC2 request and get the response.

        If the method called by the request is async it will be awaited.

        :param data: A JSON-RPC2 request.
        :param caller_details: Values passed to functions with
            dependencies and security schemes.
        :param security: Server security function details.
        :return: A valid JSON-RPC2 response.
        """
        parsed_request = parse_request(data, debug=self.debug)
        if isinstance(parsed_request, ErrorResponse):
            return parsed_request.model_dump_json()

        # Batch
        if isinstance(parsed_request, list):

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
                    caller_details,
                    security,
                    debug=self.debug,
                ).execute_async()
                if isinstance(request, RequestTypes):
                    return method_result
                return None

            results = await asyncio.gather(
                *[_process_request(it) for it in parsed_request]
            )
            return f"[{','.join(str(r) for r in results if r is not None)}]"

        # Single Request
        if parsed_request.method not in self.methods:
            if isinstance(parsed_request, (Request, ParamsRequest)):
                return _get_method_not_found_error(parsed_request)
            return None
        result = await MethodProcessor(
            self.methods[parsed_request.method],
            self.uncaught_error_code,
            parsed_request,
            caller_details,
            security,
            debug=self.debug,
        ).execute_async()

        return None if isinstance(parsed_request, NotificationTypes) else result


def _get_method_not_found_error(req: Union[NotificationType, RequestType]) -> str:
    return ErrorResponse(
        id=None if isinstance(req, NotificationTypes) else req.id,
        error=DataError(
            code=METHOD_NOT_FOUND.code,
            message=METHOD_NOT_FOUND.message,
            data=req.method,
        ),
    ).model_dump_json()
