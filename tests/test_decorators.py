"""OpenRPC method decorator tests."""
import json
import unittest

from openrpc import RPCServer

rpc = RPCServer(title="Test Decorators", version="1.0.0")


@rpc.method
def add(a: int, b: int) -> int:
    """Test plain decorator."""
    return a + b


@rpc.method(name="math.subtract")
def subtract(a: int, b: int) -> int:
    """Test decorator call with kwargs."""
    return a - b


class DecoratorTest(unittest.TestCase):
    def test_plain_decorator(self) -> None:
        req = '{"id": 1, "method": "add", "params": [1, 3], "jsonrpc": "2.0"}'
        self.assertEqual(4, json.loads(rpc.process_request(req))["result"])

    def test_kwargs_decorator(self) -> None:
        req = '{"id": 1, "method": "math.subtract", "params": [1, 3], "jsonrpc": "2.0"}'
        self.assertEqual(-2, json.loads(rpc.process_request(req))["result"])
