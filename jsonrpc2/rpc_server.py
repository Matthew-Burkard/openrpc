import inspect
import json
from json import JSONDecodeError
from typing import Callable, Optional, Union, Any

from jsonrpc2.json_types import JSONArray, JSONObject, JSON
from jsonrpc2.rpc_objects import (
    RPCRequest, RPCError, RPCResponse, PARSE_ERROR, INVALID_REQUEST,
    METHOD_NOT_FOUND, INTERNAL_ERROR, INVALID_PARAMS
)


class RPCServer:

    def __init__(self, server_error_code: Optional[int] = None) -> None:
        self.methods: dict[str, Callable] = {}
        self.server_error_code: Optional[int] = server_error_code

    def register(self, fun: Callable) -> Callable:
        self.methods[fun.__name__] = fun
        return fun

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        try:
            parsed_json = json.loads(data)
        except (TypeError, JSONDecodeError):
            return self._err(PARSE_ERROR, 'Parse error').to_json()
        if isinstance(parsed_json, dict):
            return self._process_request(parsed_json).to_json()
        elif isinstance(parsed_json, list):
            return f'[{self._process_requests(parsed_json)}]' or None
        else:
            return self._err(INVALID_REQUEST, 'Invalid request').to_json()

    def _process_requests(self, data: JSONArray) -> str:
        # TODO Configurably async or threaded request handling for
        #  better performance?
        return ','.join([self._process_request(req).to_json() for req in data])

    def _process_request(self, data: JSONObject) -> RPCResponse:
        # noinspection PyBroadException
        try:
            return self._process_method(RPCRequest(**data))
        except Exception:
            return self._err(INVALID_REQUEST, 'Invalid request')

    def _process_method(self, request: RPCRequest) -> Any:
        method = self.methods.get(request.method)
        if not method:
            return self._err(METHOD_NOT_FOUND, 'Method not found', request.id)

        result: Any = None
        # noinspection PyBroadException
        try:
            error = self._check_params(method, request.params, request.id)
            if not error:
                if isinstance(request.params, list):
                    result = method(*request.params)
                elif isinstance(request.params, dict):
                    result = method(**request.params)
                else:
                    result = method()
                result = RPCResponse(request.id, result)
        except Exception as e:
            if self.server_error_code:
                error = self._err(
                    self.server_error_code,
                    f'{type(e).__name__}: {e}',
                    request.id
                )
            else:
                error = self._err(INTERNAL_ERROR, 'Internal error', request.id)
        return error if error else result

    def _check_params(
            self,
            method: Callable,
            params: JSON,
            req_id: Union[int, str]
    ) -> Optional[RPCResponse]:
        fun_params = inspect.signature(method).parameters
        len_params = 0 if params is None else len(params)
        required = [p for _, p in fun_params.items() if self.is_required(p)]
        varargs = any(it.kind == inspect.Parameter.VAR_POSITIONAL
                      for it in fun_params.values())
        var_kwargs = any(it.kind == inspect.Parameter.VAR_KEYWORD
                         for it in fun_params.values())
        # It was a deliberate choice not to check type annotations,
        # there would be too much room for rejecting valid requests.
        if len_params < len(required):
            return self._err(INVALID_PARAMS, 'Invalid params', req_id)
        if len_params > len(fun_params.keys()) and not (varargs or var_kwargs):
            return self._err(INVALID_PARAMS, 'Invalid params', req_id)
        if isinstance(params, dict) and not var_kwargs:
            if not set(fun_params.keys()) == set(params.keys()):
                return self._err(INVALID_PARAMS, 'Invalid params', req_id)

    @staticmethod
    def _err(
            error_id: int,
            message: str,
            rpc_id: Optional[Union[str, int]] = None
    ) -> RPCResponse:
        return RPCResponse(rpc_id, error=RPCError(error_id, message))

    @staticmethod
    def is_required(param: inspect.Parameter) -> bool:
        return not param.default and param.kind not in [
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        ]
