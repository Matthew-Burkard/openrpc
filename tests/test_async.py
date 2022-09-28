"""Asynchronous OpenRPC tests."""
import asyncio
import json
import unittest
from typing import Optional, Union

from jsonrpcobjects.objects import RequestObject

from openrpc import InfoObject, RPCServer


# noinspection PyMissingOrEmptyDocstring
class RPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test JSON RPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        super(RPCTest, self).__init__(*args)

    def get_result_async(self, request: Union[str, bytes]) -> Optional[str]:
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(self.server.process_request_async(request))
        loop.close()
        return resp

    def test_that_async_is_async(self) -> None:
        wait_short_started_second = False
        wait_long_finished_second = False

        async def wait_long() -> None:
            nonlocal wait_long_finished_second, wait_short_started_second
            wait_short_started_second = False
            await asyncio.sleep(0.2)
            wait_long_finished_second = True

        async def wait_short() -> None:
            nonlocal wait_long_finished_second, wait_short_started_second
            wait_short_started_second = True
            wait_long_finished_second = False

        self.server.method(wait_long)
        self.server.method(wait_short)
        requests = ",".join(
            [
                RequestObject(id=1, method="wait_long").json(),
                RequestObject(id=2, method="wait_short").json(),
            ]
        )
        json.loads(self.get_result_async(f"[{requests}]"))
        self.assertTrue(wait_short_started_second)
        self.assertTrue(wait_long_finished_second)
        # Again in reverse order.
        wait_short_started_second = False
        wait_long_finished_second = False
        requests = ",".join(
            [
                RequestObject(id=2, method="wait_short").json(),
                RequestObject(id=1, method="wait_long").json(),
            ]
        )
        json.loads(self.get_result_async(f"[{requests}]"))
        self.assertFalse(wait_short_started_second)
        self.assertTrue(wait_long_finished_second)
