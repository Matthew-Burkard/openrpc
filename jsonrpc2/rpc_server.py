import inspect
import json
import logging
from json import JSONDecodeError
from typing import Callable, Optional, Union, Any

from jsonrpc2.json_types import JSONArray, JSONObject, JSON
from jsonrpc2.rpc_objects import (
    RPCRequest, RPCError, RPCResponse, PARSE_ERROR, INVALID_REQUEST,
    METHOD_NOT_FOUND, INTERNAL_ERROR, INVALID_PARAMS,
)

__all__ = ('RPCServer',)
log = logging.getLogger(__name__)


class RPCServer:

    def __init__(self, server_error_code: Optional[int] = None) -> None:
        self.methods: dict[str, Callable] = {}
        self.server_error_code: Optional[int] = server_error_code

    def register(self, fun: Callable) -> Callable:
        log.debug('Registering method [%s]', fun.__name__)
        self.methods[fun.__name__] = fun
        return fun

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        try:
            parsed_json = json.loads(data)
        except (TypeError, JSONDecodeError) as e:
            log.exception(f'{type(e).__name__}:')
            return self._err(PARSE_ERROR).to_json()
        if isinstance(parsed_json, dict):
            return self._process_request(parsed_json).to_json()
        elif isinstance(parsed_json, list):
            return f'[{self._process_requests(parsed_json)}]' or None
        else:
            log.error('Invalid request [%s]', parsed_json)
            return self._err(INVALID_REQUEST).to_json()

    def _process_requests(self, data: JSONArray) -> str:
        # TODO async batch handling for better performance?
        return ','.join([self._process_request(req).to_json() for req in data])

    def _process_request(self, data: JSONObject) -> RPCResponse:
        # noinspection PyBroadException
        try:
            request = RPCRequest(**data)
            try:
                len(request.params)
            except TypeError:
                return self._err(INVALID_REQUEST, request.id)
            return self._process_method(request)
        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            return self._err(INVALID_REQUEST)

    def _process_method(self, request: RPCRequest) -> Any:
        method = self.methods.get(request.method)
        if not method:
            log.error('Method not found [%s]', request)
            return self._err(METHOD_NOT_FOUND, request.id)

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
            else:
                log.error(
                    'Invalid params [%s] for method [%s]',
                    request.params,
                    method
                )
        except Exception as e:
            log.exception(f'{type(e).__name__}:')
            if self.server_error_code:
                error = self._err(
                    (self.server_error_code, 'Server error'),
                    request.id,
                    f'{type(e).__name__}: {e}'
                )
            else:
                error = self._err(INTERNAL_ERROR, request.id)
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
            return self._err(INVALID_PARAMS, req_id)
        if len_params > len(fun_params.keys()) and not (varargs or var_kwargs):
            return self._err(INVALID_PARAMS, req_id)
        if ((isinstance(params, dict) and not var_kwargs)
                and not set(fun_params.keys()) == set(params.keys())):
            return self._err(INVALID_PARAMS, req_id)

    @staticmethod
    def _err(
            err: tuple[int, str],
            rpc_id: Optional[Union[str, int]] = None,
            data: Optional[Any] = None
    ) -> RPCResponse:
        return RPCResponse(rpc_id, error=RPCError(err[0], err[1], data))

    @staticmethod
    def is_required(param: inspect.Parameter) -> bool:
        return not param.default and param.kind not in [
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD
        ]
