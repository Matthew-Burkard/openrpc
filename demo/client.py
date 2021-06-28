import uuid
from typing import Union

from json_types import JSON
from rpc_objects import RPCError, RPCRequest, RPCResponse
from rpc_server import RPCServer


def get_uuid() -> str:
    return str(uuid.uuid4())


class MathRPCClient:

    def __init__(self, server: RPCServer):
        self.server = server

    def add(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('add', [x, y], str(uuid.uuid4())))

    def subtract(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('subtract', [x, y], str(uuid.uuid4())))

    def divide(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('divide', [x, y], str(uuid.uuid4())))

    def _call(self, request: RPCRequest) -> Union[JSON, RPCError]:
        resp = RPCResponse.from_json(self.server.process(request.to_json()))
        return resp.error if resp.error else resp.result
