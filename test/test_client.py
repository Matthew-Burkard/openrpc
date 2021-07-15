import unittest
import uuid
from typing import Union

from jsonrpc2.rpc_client import RPCDirectClient
from jsonrpc2.rpc_objects import RPCError, RPCRequest
from jsonrpc2.rpc_server import RPCServer


class TestRPCClient(RPCDirectClient):

    def add(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('add', [x, y], str(uuid.uuid4())), )

    def subtract(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('subtract', [x, y], str(uuid.uuid4())), )

    def divide(self, x: float, y: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('divide', [x, y], str(uuid.uuid4())), )

    def echo(self, x: float) -> Union[float, RPCError]:
        return self._call(RPCRequest('echo', [x], str(uuid.uuid4())), )


test_rpc = RPCServer(-32000)


@test_rpc.register
def echo(x: float) -> float:
    return x


class RPCClientTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.client = TestRPCClient(test_rpc)
        super(RPCClientTest, self).__init__(*args)

    def test_client(self) -> None:
        self.assertEqual(9, self.client.echo(9))
