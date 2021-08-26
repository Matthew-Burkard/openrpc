import json
import unittest
from dataclasses import dataclass
from typing import Union

from openrpc.rpc_objects import RequestObject
from openrpc.server import OpenRPCServer


@dataclass
class Vector3:
    x: float
    y: float
    z: float


class OpenRPCTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.server = OpenRPCServer('Open RPC Test Server', '1.0.0')
        self.server.method(increment)
        self.server.method(get_distance)
        super(OpenRPCTest, self).__init__(*args)

    def test_list_param(self) -> None:
        request = RequestObject(id=1, method='rpc.discover')
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(
            resp['result'],
            {
                'openrpc': '1.2.6',
                'info': {'title': 'Open RPC Test Server', 'version': '1.0.0'},
                'methods': [{
                    'name': 'increment', 'params': [{
                        'name': 'numbers',
                        'schema': {
                            'type': 'array',
                            'items': {'type': 'number'}
                        },
                        'required': False
                    }],
                    'result': {
                        'name': 'result',
                        'schema': {
                            'type': 'array',
                            'items': {'type': ['number', 'string']}
                        },
                        'required': False
                    }
                }, {
                    'name': 'get_distance', 'params': [{
                        'name': 'position',
                        'schema': {'$ref': '#/components/schemas/Vector3'},
                        'required': False
                    }, {
                        'name': 'target',
                        'schema': {'$ref': '#/components/schemas/Vector3'},
                        'required': False
                    }],
                    'result': {
                        'name': 'result',
                        'schema': {'$ref': '#/components/schemas/Vector3'},
                        'required': False
                    }
                }],
                'components': {
                    'schemas': {
                        'Vector3': {
                            'type': 'object', 'properties': {
                                'x': {'type': 'number'},
                                'y': {'type': 'number'},
                                'z': {'type': 'number'}
                            }
                        }
                    }
                }
            }
        )


def increment(numbers: list[Union[int, float]]) -> list[Union[int, str]]:
    return [it + 1 for it in numbers]


def get_distance(position: Vector3, target: Vector3) -> Vector3:
    return Vector3(
        position.x - target.x,
        position.y - target.y,
        position.z - target.z,
    )
