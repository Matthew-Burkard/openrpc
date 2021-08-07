import unittest
import uuid
from typing import Union

from openrpc.rpc_client import RPCDirectClient
from openrpc.rpc_objects import ErrorResponseObject, RequestObjectParams
# noinspection PyProtectedMember
from openrpc._rpc_server import RPCServer

test_rpc = RPCServer(-32000)


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
        self.client = TestRPCClient(test_rpc)
        super(RPCClientTest, self).__init__(*args)

    def test_client(self) -> None:
        self.assertEqual(9, self.client.echo(9))
