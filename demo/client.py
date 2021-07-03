import uuid
from typing import Union, Any

from jsonrpc2.rpc_client import RPCClient
from jsonrpc2.rpc_objects import RPCError, RPCRequest
from jsonrpc2.rpc_server import RPCServer


def get_uuid() -> str:
    return str(uuid.uuid4())


class MathRPCClient(RPCClient):

    def __init__(self, server: RPCServer):
        self.server = server

    def add(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('add', [x, y], str(uuid.uuid4())))

    def subtract(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('subtract', [x, y], str(uuid.uuid4())))

    def divide(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('divide', [x, y], str(uuid.uuid4())))

    def _call(self, request: RPCRequest) -> Any:
        return self._handle_json(self.server.process(request.to_json()))
