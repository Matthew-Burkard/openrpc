import abc
import logging
import uuid
from json import JSONDecodeError
from typing import Any, Union, Type, Optional, Callable

from jsonrpc2.exceptions import get_exception, JSONRPCError, ServerError
from jsonrpc2.rpc_objects import RPCRequest, RPCResponse

__all__ = ('RPCClient', 'RPCDirectClient')

from jsonrpc2.rpc_server import RPCServer

log = logging.getLogger(__name__)


class RPCClient(abc.ABC):

    @property
    def server_errors(self) -> dict[int, Type]:
        return {}

    @staticmethod
    def _gen_id() -> Union[str, int]:
        return str(uuid.uuid4())

    @abc.abstractmethod
    def _call(
            self,
            request: RPCRequest,
            deserializer: Optional[Callable] = None
    ) -> Any: ...

    def _handle_json(self, data: Union[bytes, str]) -> Any:
        try:
            resp = RPCResponse.from_json(data)
            if resp.error:
                if -32000 >= resp.error.code > -32100:
                    er = self.server_errors.get(resp.error.code) or ServerError
                    raise er(resp.error)
                raise get_exception(resp.error.code)
            return resp.result
        except (JSONDecodeError, TypeError, AttributeError) as e:
            log.exception(f'{type(e).__name__}:')
            raise JSONRPCError('Unable to parse response.')


class RPCDirectClient(RPCClient):
    def __init__(self, server: RPCServer):
        self.server = server

    def _call(
            self,
            request: RPCRequest,
            deserializer: Optional[Callable] = None
    ) -> Any:
        return self._handle_json(self.server.process(request.to_json()))
