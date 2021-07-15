import uuid
from typing import Union

from jsonrpc2.rpc_client import RPCDirectClient
from jsonrpc2.rpc_objects import RPCError, RPCRequest


class MathRPCClient(RPCDirectClient):

    def add(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('add', [x, y], str(uuid.uuid4())), )

    def subtract(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('subtract', [x, y], str(uuid.uuid4())), )

    def divide(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('divide', [x, y], str(uuid.uuid4())), )
