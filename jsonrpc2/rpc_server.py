import json
import logging
from json import JSONDecodeError
from typing import Callable, Optional, Union, Any

from jsonrpc2.rpc_objects import (
    PARSE_ERROR, ErrorResponseObject,
    ErrorObjectData, ErrorObject, ResponseType, INVALID_REQUEST, RequestType,
    RequestObjectParams, RequestObject, NotificationObjectParams,
    NotificationObject, METHOD_NOT_FOUND, ResultResponseObject, INTERNAL_ERROR,
)

__all__ = ('RPCServer',)
log = logging.getLogger(__name__)


class RPCServer:

    def __init__(self, uncaught_error_code: Optional[int] = None) -> None:
        self.methods: dict[str, Callable] = {}
        self.uncaught_error_code: Optional[int] = uncaught_error_code

    def register(self, fun: Callable) -> Callable:
        log.debug('Registering method [%s]', fun.__name__)
        self.methods[fun.__name__] = fun
        return fun

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
        method = self.methods.get(request.method)
        if not method:
            log.error('Method not found [%s]', request)
            return self._err(METHOD_NOT_FOUND, request.id)

        # noinspection PyBroadException
        try:
            # Call method.
            if isinstance(request.params, list):
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
            return self._err(INTERNAL_ERROR, request.id, )

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
