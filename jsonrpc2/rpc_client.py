import abc
import json
import logging
import sys
from json import JSONDecodeError
from random import randint
from typing import Any, Union, Type, Optional, Callable

from jsonrpc2.exceptions import get_exception, JSONRPCError, ServerError

__all__ = ('RPCClient', 'RPCDirectClient')

from jsonrpc2.rpc_server import RPCServer
from rpc_objects import (
    RequestType, ResponseType, ResultResponseObject, ErrorResponseObject,
)

log = logging.getLogger(__name__)


class RPCClient(abc.ABC):

    @property
    def server_errors(self) -> dict[int, Type]:
        return {}

    @staticmethod
    def _gen_id() -> Union[str, int]:
        return randint(1, sys.maxsize)

    @abc.abstractmethod
    def _call(
            self,
            request: RequestType,
            deserializer: Optional[Callable] = None
    ) -> Any: ...

    def _handle_json(self, data: Union[bytes, str]) -> Any:
        resp = self._parse_response(data)
        if isinstance(resp, ResultResponseObject):
            return resp.result
        if -32000 >= resp.error.code > -32100:
            error = self.server_errors.get(resp.error.code) or ServerError
            raise error(resp.error)
        raise get_exception(resp.error.code)

    @staticmethod
    def _parse_response(data: Union[bytes, str]) -> ResponseType:
        try:
            resp = json.loads(data)
            if resp.get('error'):
                return ErrorResponseObject.from_dict(resp)
            if resp.get('result'):
                return ResultResponseObject.from_dict(resp)
            raise JSONRPCError('Unable to parse response.')
        except (JSONDecodeError, TypeError, AttributeError) as e:
            log.exception(f'{type(e).__name__}:')
            raise JSONRPCError('Unable to parse response.')


class RPCDirectClient(RPCClient):
    def __init__(self, server: RPCServer):
        self.server = server

    def _call(
            self,
            request: RequestType,
            deserializer: Optional[Callable] = None
    ) -> Any:
        return self._handle_json(self.server.process(request.to_json()))
