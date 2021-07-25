import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Callable, Optional, Union, Any

import util
from open_rpc_objects import MethodObject, TagObject, OpenRPCObject, InfoObject
from openrpc.rpc_objects import (
    PARSE_ERROR, ErrorResponseObject, ErrorObjectData, ErrorObject,
    ResponseType, INVALID_REQUEST, RequestType, RequestObjectParams,
    RequestObject, NotificationObjectParams, NotificationObject,
    METHOD_NOT_FOUND, ResultResponseObject, INTERNAL_ERROR,
)

__all__ = ('RPCServer',)
log = logging.getLogger(__name__)


@dataclass
class RegisteredMethod:
    fun: Callable
    method: MethodObject


class RPCServer:

    def __init__(
            self,
            title: str,
            version: str,
            uncaught_error_code: Optional[int] = None
    ) -> None:
        self.title = title
        self.version = version
        self.methods: dict[str, RegisteredMethod] = {}
        self.uncaught_error_code: Optional[int] = uncaught_error_code
        self.method(MethodObject('rpc.discover'))(self._get_discover_method)

    def method(self, method: Optional[MethodObject] = None) -> Callable:
        method = method or MethodObject()

        def register(fun: Callable) -> Callable:
            log.debug('Registering method [%s]', fun.__name__)
            method.name = method.name or fun.__name__
            method.params = method.params or util.get_openrpc_params(fun)
            method.result = method.result or util.get_openrpc_result(fun)
            method.tags = method.tags or [TagObject('name of module')]  # TODO
            self.methods[method.name] = RegisteredMethod(fun, method)
            return fun

        return register

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        # Parse JSON
        try:
            parsed_json = json.loads(data)
        except (TypeError, JSONDecodeError) as e:
            log.exception(f'{type(e).__name__}:')
            return self._err(PARSE_ERROR).to_json()

        # Process as single request or batch.
        # noinspection PyBroadException
        try:
            if isinstance(parsed_json, dict):
                return self._process_request(parsed_json).to_json()
            if isinstance(parsed_json, list):
                return f'[{self._process_requests(parsed_json)}]' or None
        except Exception:
            log.error('Invalid request [%s]', parsed_json)
            return self._err(INVALID_REQUEST).to_json()

        # Request must be a JSON primitive.
        log.error('Invalid request [%s]', parsed_json)
        return self._err(INVALID_REQUEST).to_json()

    def _process_requests(self, data: list) -> str:
        # TODO async batch handling for better performance?
        return ','.join([self._process_request(req).to_json() for req in data])

    def _process_request(self, data: dict) -> Optional[ResponseType]:
        request = self._get_request(data)
        # noinspection PyBroadException
        try:
            return self._process_method(request)
        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            return self._err(INVALID_REQUEST)

    def _process_method(self, request: RequestType) -> Any:
        registered_method = self.methods.get(request.method)
        if not registered_method:
            log.error('Method not found [%s]', request)
            return self._err(METHOD_NOT_FOUND, request.id)

        # noinspection PyBroadException
        try:
            method = registered_method.fun
            # Call method.
            if (isinstance(request, RequestObject)
                    or isinstance(request, NotificationObject)):
                result = method()
            elif isinstance(request.params, list):
                result = method(*request.params)
            elif isinstance(request.params, dict):
                result = method(**request.params)
            else:
                result = method()

            # Return proper response object.
            if (isinstance(request, NotificationObject)
                    or isinstance(request, NotificationObjectParams)):
                return None
            if (isinstance(result, ErrorObjectData)
                    or isinstance(result, ErrorObject)):
                return ErrorResponseObject(request.id, result)
            return ResultResponseObject(request.id, result)

        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            if self.uncaught_error_code:
                return self._err(
                    (self.uncaught_error_code, 'Server error'),
                    request.id,
                    f'{type(e).__name__}: {e}'
                )
            return self._err(INTERNAL_ERROR, request.id)

    def _get_discover_method(self) -> OpenRPCObject:
        return OpenRPCObject(
            InfoObject(self.title, self.version),
            [it.method for it in self.methods.values()
             if it.method.name != 'rpc.discover']
        )

    @staticmethod
    def _get_request(data: dict) -> RequestType:
        if data.get('id'):
            return (
                RequestObjectParams if data.get('params') else RequestObject
            ).from_dict(data)
        return (
            NotificationObjectParams
            if data.get('params') else
            NotificationObject
        ).from_dict(data)

    @staticmethod
    def _err(
            err: tuple[int, str],
            rpc_id: Optional[Union[str, int]] = None,
            data: Optional[Any] = None
    ) -> ErrorResponseObject:
        if data:
            error = ErrorObjectData(err[0], err[1], data)
            return ErrorResponseObject(rpc_id, error)
        return ErrorResponseObject(rpc_id, ErrorObject(err[0], err[1]))
