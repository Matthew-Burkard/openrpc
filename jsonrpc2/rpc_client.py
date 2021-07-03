import abc
from json import JSONDecodeError
from typing import Any, Union, Type

from jsonrpc2.exceptions import get_exception, JSONRPCError, ServerError
from jsonrpc2.rpc_objects import RPCRequest, RPCResponse


class RPCClient(abc.ABC):

    @property
    def server_errors(self) -> dict[int, Type]:
        return {}

    @abc.abstractmethod
    def _call(self, request: RPCRequest) -> Any: ...

    def _handle_json(self, data: Union[bytes, str]) -> Any:
        try:
            resp = RPCResponse.from_json(data)
            if resp.error:
                if -32000 >= resp.error.code > -32100:
                    er = self.server_errors.get(resp.error.code) or ServerError
                    raise er(resp.error)
                raise get_exception(resp.error.code)
            return resp.result
        except (JSONDecodeError, TypeError, AttributeError):
            raise JSONRPCError('Unable to parse response.')
