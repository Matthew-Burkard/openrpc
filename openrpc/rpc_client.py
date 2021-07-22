import abc
import logging
import sys
from random import randint
from typing import Any, Union, Type

import util
from openrpc.exceptions import get_exception, ServerError
from openrpc.rpc_server import RPCServer
from rpc_objects import RequestType, ResultResponseObject

__all__ = ('RPCClient', 'RPCDirectClient')
log = logging.getLogger(__name__)


class RPCClient(abc.ABC):

    @property
    def server_errors(self) -> dict[int, Type]:
        return {}

    @staticmethod
    def _gen_id() -> Union[str, int]:
        return randint(1, sys.maxsize)

    @abc.abstractmethod
    def _call(self, request: RequestType) -> Any: ...

    def _handle_json(self, data: Union[bytes, str]) -> Any:
        resp = util.parse_response(data)
        if isinstance(resp, ResultResponseObject):
            return resp.result
        if -32000 >= resp.error.code > -32100:
            error = self.server_errors.get(resp.error.code) or ServerError
            raise error(resp.error)
        raise get_exception(resp.error.code)


class RPCDirectClient(RPCClient):
    def __init__(self, server: RPCServer):
        self.server = server

    def _call(self, request: RequestType) -> Any:
        return self._handle_json(self.server.process(request.to_json()))
