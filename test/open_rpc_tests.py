import json
import unittest
from typing import Union

from openrpc.openrpc_server import OpenRPCServer
from openrpc.rpc_objects import RequestObject


class OpenRPCTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.server = OpenRPCServer('Open RPC Test Server', '1.0.0')
        self.server.method(increment_list)
        super(OpenRPCTest, self).__init__(*args)

    def test_list_param(self) -> None:
        request = RequestObject(id=1, method='rpc.discover')
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(
            resp,
            {
                'id': '1',
                'result': {
                    'openrpc': '1.2.6',
                    'info': {
                        'title': 'Open RPC Test Server',
                        'version': '1.0.0'
                    },
                    'methods': [{
                        'name': 'increment_list',
                        'params': [{
                            'name': 'numbers',
                            'schema': {'type': 'array'},
                            'required': False
                        }],
                        'result': {
                            'name': 'result',
                            'schema': {'type': 'array'}
                        }
                    }]
                }
            }
        )


def increment_list(numbers: list[Union[int, float]]) -> list:
    return [it + 1 for it in numbers]
