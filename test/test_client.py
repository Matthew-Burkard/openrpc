import unittest
import uuid
from typing import Union

from openrpc.rpc_client import RPCDirectClient
from openrpc.rpc_objects import ErrorResponseObject, RequestObjectParams
from server import OpenRPCServer

test_rpc = OpenRPCServer('Test Client', '1.0.0', -32000)


class TestRPCClient(RPCDirectClient):

    def echo(self, x: float) -> Union[float, list, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(
                id=str(uuid.uuid4()),
                method='echo',
                params=[x]
            )
        )


@test_rpc.method
def echo(x: float) -> Union[float, tuple]:
    return x


class RPCClientTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.client = TestRPCClient(test_rpc.server)
        super(RPCClientTest, self).__init__(*args)

    def test_client(self) -> None:
        self.assertEqual(9, self.client.echo(9))
