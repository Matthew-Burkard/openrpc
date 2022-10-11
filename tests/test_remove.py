"""Test removing a method from a server."""
import unittest

from openrpc import InfoObject, RPCServer


# noinspection PyUnusedLocal
def add(a: int, b: int) -> int:
    """pass"""


class TestRemove(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test JSON RPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        self.server.method(add)
        super(TestRemove, self).__init__(*args)

    def test_remove(self) -> None:
        self.server.remove("add")
        self.assertEqual(0, len(self.server.methods))
