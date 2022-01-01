"""Provides RequestProcessor class for processing a single request."""
import inspect
import logging
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

from jsonrpcobjects.errors import INTERNAL_ERROR
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


class RequestProcessor:
    """Execute a JSON-RPC2 request and get the response."""

    def __init__(
        self,
        method: Callable,
        uncaught_error_code: Optional[int],
        request: Union[RequestType, NotificationType],
    ) -> None:
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

        except Exception as e:
            return self._get_error_response(e)

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

        except Exception as e:
            return self._get_error_response(e)

    def _execute(self) -> Any:
        annotations = get_type_hints(self.method)
        params = None
        # Call method.
        if isinstance(self.request, (RequestObject, NotificationObject)):
            result = self.method()
        elif isinstance(self.request.params, list):
            params = self._get_list_params(self.request.params, annotations)
            result = self.method(*params)
        else:
            params = self._get_dict_params(self.request.params, annotations)
            result = self.method(**params)

        # Logging
        id_msg = ""
        res_msg = ""
        if isinstance(self.request, (RequestObject, RequestObjectParams)):
            res_msg = f" {result}"
            if isinstance(self.request.id, str):
                id_msg = f'"{self.request.id}" '
            else:
                id_msg = f"{self.request.id} "
        params_msg = f" {params}" if params is not None else ""
        log.info('%s--> "%s"%s -->%s', id_msg, self.request.method, params_msg, res_msg)
        return result

    def _get_error_response(self, e: Exception):
        log.exception(f"{type(e).__name__}:")
        if self.uncaught_error_code:
            return ErrorResponseObject(
                id=self.request.id,
                error=ErrorObjectData(
                    code=self.uncaught_error_code,
                    message="Server error",
                    data=f"{type(e).__name__}: {e}",
                ),
            ).json()
        return ErrorResponseObject(id=self.request.id, error=INTERNAL_ERROR).json()

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
