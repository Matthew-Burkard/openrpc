import unittest
import uuid
from typing import Union

from openrpc.rpc_client import RPCDirectClient
from openrpc.rpc_objects import ErrorResponseObject, RequestObjectParams
from openrpc.rpc_server import RPCServer

test_rpc = RPCServer('Test RPC Server', '1.0.0', -32000)


class TestRPCClient(RPCDirectClient):

    def echo(self, x: float) -> Union[float, list, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(str(uuid.uuid4()), 'echo', [x])
        )


@test_rpc.method
def echo(x: float) -> Union[float, tuple]:
    return x


class RPCClientTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.client = TestRPCClient(test_rpc)
        super(RPCClientTest, self).__init__(*args)

    def test_client(self) -> None:
        self.assertEqual(9, self.client.echo(9))
        print(self.client.echo(5))
