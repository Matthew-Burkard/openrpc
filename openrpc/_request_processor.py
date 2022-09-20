"""Provides RequestProcessor class for processing a single request."""
import inspect
import logging
from enum import Enum
from typing import (
    Any,
    Callable,
    get_args,
    get_origin,
    get_type_hints,
    Optional,
    Type,
    Union,
)

from jsonrpcobjects.errors import INTERNAL_ERROR, InternalError, JSONRPCError
from jsonrpcobjects.objects import (
    ErrorObjectData,
    ErrorResponseObject,
    NotificationObject,
    NotificationObjectParams,
    NotificationType,
    RequestObject,
    RequestObjectParams,
    RequestType,
    ResultResponseObject,
)

__all__ = ("RequestProcessor",)

log = logging.getLogger("openrpc")


class DeserializationError(InternalError):
    """Raised when a request param cannot be deserialized."""

    def __init__(self, param: Any, p_type: Any) -> None:
        msg = f"Failed to deserialize request param [{param}] to type [{p_type}]"
        super().__init__(ErrorObjectData(**{**INTERNAL_ERROR.dict(), **{"data": msg}}))


class NotDeserializedType:
    """Returned by deserialization method if deserialization fails.

    The deserialized value may very well be False or None, so a custom
    type needs to be made to represent a failure to deserialize.
    """


NotDeserialized = NotDeserializedType()


class RequestProcessor:
    """Execute a JSON-RPC2 request and get the response."""

    def __init__(
        self,
        method: Callable,
        uncaught_error_code: int,
        request: Union[RequestType, NotificationType],
    ) -> None:
        """Init a request processor.

        :param method: The Python callable.
        :param uncaught_error_code: Code for errors raised by method.
        :param request: Request to execute.
        """
        self.method = method
        self.request = request
        self.uncaught_error_code = uncaught_error_code

    def execute(self) -> Optional[str]:
        """Execute the method and get the JSON-RPC2 response."""
        try:
            result = self._execute()
            if isinstance(self.request, (NotificationObject, NotificationObjectParams)):
                # If request was notification, return nothing.
                return None
            return ResultResponseObject(id=self.request.id, result=result).json()

        except Exception as error:
            return self._get_error_response(error)

    async def execute_async(self) -> Any:
        """Execute the method and get the JSON-RPC2 response.

        If the method is an async method it will be awaited.
        """
        try:
            result = self._execute()
            if inspect.isawaitable(result):
                result = await result
            if isinstance(self.request, (NotificationObject, NotificationObjectParams)):
                # If request was notification, return nothing.
                return None
            return ResultResponseObject(id=self.request.id, result=result).json()

        except Exception as error:
            return self._get_error_response(error)

    def _execute(self) -> Any:
        annotations = get_type_hints(self.method)
        params: Optional[Union[dict, list]]
        params_msg = ""
        # Call method.
        if isinstance(self.request, (RequestObject, NotificationObject)):
            result = self.method()
        elif isinstance(self.request.params, list):
            params = self._get_list_params(self.request.params, annotations)
            result = self.method(*params)
            params_msg = ", ".join(str(p) for p in params)
        else:
            params = self._get_dict_params(self.request.params, annotations)
            result = self.method(**params)
            params_msg = ", ".join(f"{k}={v}" for k, v in params.items())

        # Logging
        id_msg = "None"
        if isinstance(self.request, (RequestObject, RequestObjectParams)):
            if isinstance(self.request.id, str):
                id_msg = f'"{self.request.id}"'
            else:
                id_msg = str(self.request.id)
        log.info("%s: %s(%s) -> %s", id_msg, self.request.method, params_msg, result)
        return result

    def _get_error_response(self, error: Exception) -> Optional[str]:
        log.exception("%s:", type(error).__name__)
        if not isinstance(self.request, (RequestObjectParams, RequestObject)):
            return None
        if isinstance(error, JSONRPCError):
            return ErrorResponseObject(id=self.request.id, error=error.rpc_error).json()
        return ErrorResponseObject(
            id=self.request.id,
            error=ErrorObjectData(
                code=self.uncaught_error_code,
                message="Server error",
                data=f"{type(error).__name__}: {error}",
            ),
        ).json()

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
        res = self._deserialize_param(param, p_type)
        if res is NotDeserialized:
            raise DeserializationError(param, p_type)
        return res

    def _deserialize_param(self, param: Any, p_type: Type) -> Any:
        try:
            if isinstance(p_type, type) and issubclass(p_type, Enum):
                return p_type(param)
            if get_origin(p_type) == Union:
                for arg in get_args(p_type):
                    res = self._deserialize_param(param, arg)
                    if res is NotDeserialized:
                        continue
                    return res
            if get_origin(p_type) == list:
                types = get_args(p_type)
                return [self._deserialize_param(it, types[0]) for it in param]
            try:
                return p_type(**param)
            except (TypeError, AttributeError, KeyError):
                return p_type(param)
        except (TypeError, AttributeError, KeyError, ValueError):
            return NotDeserialized
