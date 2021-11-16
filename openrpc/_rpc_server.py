import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import (
    Any,
    Callable,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from jsonrpcobjects.errors import INTERNAL_ERROR, INVALID_REQUEST, PARSE_ERROR
from jsonrpcobjects.objects import (
    ErrorObjectData,
    ErrorResponseObject,
    NotificationObject,
    NotificationObjectParams,
    NotificationType,
    RequestObject,
    RequestObjectParams,
    RequestType,
    ResponseType,
    ResultResponseObject,
)

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
        # Parse JSON
        try:
            parsed_json = json.loads(data)
        except (TypeError, JSONDecodeError) as e:
            log.exception(f"{type(e).__name__}:")
            return ErrorResponseObject(error=PARSE_ERROR).json()

        # Process as single request or batch.
        try:
            if isinstance(parsed_json, dict) and parsed_json.get("id"):
                return self._process_request(parsed_json).json()
            elif isinstance(parsed_json, dict) and not parsed_json.get("id"):
                self._process_request(parsed_json)
                return None
            if isinstance(parsed_json, list):
                return f"[{self._process_requests(parsed_json)}]" or None
        except Exception as e:
            log.error("Invalid request [%s]", parsed_json)
            log.exception(f"{type(e).__name__}:")
            return ErrorResponseObject(error=INVALID_REQUEST).json()

        # Request must be a JSON primitive.
        log.error("Invalid request [%s]", parsed_json)
        return ErrorResponseObject(error=INVALID_REQUEST).json()

    def _process_requests(self, data: list) -> str:
        # TODO async batch handling for better performance?
        # Process notifications.
        [self._process_request(req) for req in data if not req.get("id")]
        # Return request responses.
        return ",".join(
            [self._process_request(req).json() for req in data if req.get("id")]
        )

    def _process_request(self, data: dict) -> Optional[ResponseType]:
        request = self._get_request(data)
        try:
            return self._process_method(request)
        except Exception as e:
            log.exception(f"{type(e).__name__}:")
            return ErrorResponseObject(error=INVALID_REQUEST)

    def _process_method(self, request: Union[RequestType, NotificationType]) -> Any:
        registered_method = self.methods.get(request.method)
        if not registered_method:
            log.error("Method not found [%s]", request)
            if isinstance(request, (RequestObject, RequestObjectParams)):
                return ErrorResponseObject(
                    id=request.id,
                    error=ErrorObjectData(
                        code=-32601, message="Method not found", data=request.method
                    ),
                )

        try:
            method = registered_method.fun
            # noinspection PyUnresolvedReferences
            annotations = get_type_hints(method)

            # Call method.
            if isinstance(request, (RequestObject, NotificationObject)):
                result = method()
            elif isinstance(request.params, list):
                result = method(*self._get_list_params(request.params, annotations))
            elif isinstance(request.params, dict):
                result = method(**self._get_dict_params(request.params, annotations))
            else:
                result = method()

            # Return proper response object.
            if isinstance(request, (NotificationObject, NotificationObjectParams)):
                # If request was notification, return nothing.
                return None
            return ResultResponseObject(id=request.id, result=result)

        except Exception as e:
            log.exception(f"{type(e).__name__}:")
            if self.uncaught_error_code:
                return ErrorResponseObject(
                    id=request.id,
                    error=ErrorObjectData(
                        code=self.uncaught_error_code,
                        message="Server error",
                        data=f"{type(e).__name__}: {e}",
                    ),
                )
            return ErrorResponseObject(id=request.id, error=INTERNAL_ERROR)

    def _get_list_params(self, params: list, annotations: dict) -> list:
        try:
            return [
                self._deserialize(p, list(annotations.values())[i])
                for i, p in enumerate(params)
            ]
        except IndexError:
            return params

    def _get_dict_params(self, params: dict, annotations: dict) -> dict:
        try:
            return {k: self._deserialize(p, annotations[k]) for k, p in params.items()}
        except KeyError:
            return params

    def _deserialize(self, param: Any, p_type: Type) -> Any:
        """Deserialize dict to python objects."""
        if get_origin(p_type) == Union:
            for arg in get_args(p_type):
                try:
                    return self._deserialize(param, arg)
                except TypeError:
                    continue
        if get_origin(p_type) == list:
            types = get_args(p_type)
            return [self._deserialize(it, types[0]) for it in param]
        if not isinstance(param, dict):
            return param
        try:
            return p_type(**param)
        except (TypeError, AttributeError, KeyError):
            return param

    @staticmethod
    def _get_request(data: dict) -> Union[RequestType, NotificationType]:
        if data.get("id"):
            return (RequestObjectParams if data.get("params") else RequestObject)(
                **data
            )
        return (NotificationObjectParams if data.get("params") else NotificationObject)(
            **data
        )
