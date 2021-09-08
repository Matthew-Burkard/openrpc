import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Callable, Optional, Union, Any, Type

from jsonrpcobjects.errors import (
    PARSE_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    INTERNAL_ERROR,
)
from jsonrpcobjects.objects import (
    ErrorResponseObject,
    ErrorObjectData,
    ResponseType,
    RequestType,
    RequestObjectParams,
    RequestObject,
    NotificationObjectParams,
    NotificationObject,
    ResultResponseObject,
    NotificationType,
    ErrorObject,
)

from openrpc.objects import MethodObject

__all__ = ('RPCServer',)
T = Type[Callable]
log = logging.getLogger(__name__)


@dataclass
class RegisteredMethod:
    fun: Callable
    method: MethodObject


class RPCServer:

    def __init__(self, uncaught_error_code: Optional[int] = None) -> None:
        self.methods: dict[str, RegisteredMethod] = {}
        self.uncaught_error_code: Optional[int] = uncaught_error_code

    def method(self, func: T, method: MethodObject) -> T:
        log.debug('Registering method [%s]', func.__name__)
        method.name = method.name or func.__name__
        self.methods[method.name] = RegisteredMethod(func, method)
        return func

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        # Parse JSON
        try:
            parsed_json = json.loads(data)
        except (TypeError, JSONDecodeError) as e:
            log.exception(f'{type(e).__name__}:')
            return ErrorResponseObject(error=PARSE_ERROR).json(by_alias=True)

        # Process as single request or batch.
        try:
            if isinstance(parsed_json, dict):
                return self._process_request(parsed_json).json(by_alias=True)
            if isinstance(parsed_json, list):
                return f'[{self._process_requests(parsed_json)}]' or None
        except Exception as e:
            log.error('Invalid request [%s]', parsed_json)
            log.exception(f'{type(e).__name__}:')
            return ErrorResponseObject(
                error=INVALID_REQUEST
            ).json(by_alias=True)

        # Request must be a JSON primitive.
        log.error('Invalid request [%s]', parsed_json)
        return ErrorResponseObject(error=INVALID_REQUEST).json(by_alias=True)

    def _process_requests(self, data: list) -> str:
        # TODO async batch handling for better performance?
        return ','.join(
            [self._process_request(req).json(by_alias=True)
             for req in data]
        )

    def _process_request(self, data: dict) -> Optional[ResponseType]:
        request = self._get_request(data)
        try:
            return self._process_method(request)
        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            return ErrorResponseObject(error=INVALID_REQUEST)

    def _process_method(self, request: RequestType) -> Any:
        registered_method = self.methods.get(request.method)
        if not registered_method:
            log.error('Method not found [%s]', request)
            return ErrorResponseObject(id=request.id, error=METHOD_NOT_FOUND)

        try:
            method = registered_method.fun
            # noinspection PyUnresolvedReferences
            annotations = method.__annotations__

            # Call method.
            if isinstance(request, (RequestObject, NotificationObject)):
                result = method()
            elif isinstance(request.params, list):
                result = method(
                    *self._get_list_params(request.params, annotations)
                )
            elif isinstance(request.params, dict):
                result = method(
                    **self._get_dict_params(request.params, annotations)
                )
            else:
                result = method()

            # Return proper response object.
            if isinstance(
                    request, (NotificationObject, NotificationObjectParams)
            ):
                return None
            if isinstance(result, (ErrorObjectData, ErrorObject)):
                return ErrorResponseObject(id=request.id, result=result)
            return ResultResponseObject(id=request.id, result=result)

        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            if self.uncaught_error_code:
                return ErrorResponseObject(
                    id=request.id,
                    error=ErrorObjectData(
                        code=self.uncaught_error_code,
                        message='Server error',
                        data=f'{type(e).__name__}: {e}'
                    )
                )
            return ErrorResponseObject(id=request.id, error=INTERNAL_ERROR)

    def _get_list_params(self, params: list, annotations: dict) -> list:
        try:
            return [self._deserialize_param(p, list(annotations.values())[i])
                    for i, p in enumerate(params)]
        except IndexError:
            return params

    def _get_dict_params(self, params: dict, annotations: dict) -> dict:
        try:
            return {k: self._deserialize_param(p, annotations[k])
                    for k, p in params.items()}
        except KeyError:
            return params

    def _deserialize_param(self, param: Any, p_type: Type) -> Any:
        if not isinstance(param, dict):
            return param
        return p_type(
            **{k: self._deserialize_param(v, type(p_type.__annotations__[k]))
               for k, v in param.items()}
        )

    @staticmethod
    def _get_request(data: dict) -> Union[RequestType, NotificationType]:
        if data.get('id'):
            return (
                RequestObjectParams if data.get('params') else RequestObject
            )(**data)
        return (
            NotificationObjectParams
            if data.get('params') else
            NotificationObject
        )(**data)
