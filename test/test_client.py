import unittest
import uuid
from typing import Union

from jsonrpc2.rpc_client import RPCDirectClient
from jsonrpc2.rpc_objects import RPCError, RPCRequest
from jsonrpc2.rpc_server import RPCServer


class TestRPCClient(RPCDirectClient):

    def echo(self, x: float, **kwargs) -> Union[float, list, RPCError]:
        return self._call(RPCRequest('echo', [x, kwargs], str(uuid.uuid4())))


test_rpc = RPCServer(-32000)


@test_rpc.register
def echo(x: float, **kwargs) -> Union[float, tuple]:
    if kwargs:
        return x, kwargs
    return x


class RPCClientTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.client = TestRPCClient(test_rpc)
        super(RPCClientTest, self).__init__(*args)

    def test_client(self) -> None:
        self.assertEqual(9, self.client.echo(9))
        print(self.client.echo(5, coffee='mocha'))
