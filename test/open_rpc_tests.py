import json
import unittest
from dataclasses import dataclass
from typing import Union

from openrpc.openrpc_server import OpenRPCServer
from openrpc.rpc_objects import RequestObject


@dataclass
class Vector3:
    x: float
    y: float
    z: float


class OpenRPCTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.server = OpenRPCServer('Open RPC Test Server', '1.0.0')
        self.server.method(increment_list)
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
                            'schema': {
                                'type': 'array'
                            },
                            'required': False
                        }],
                        'result': {
                            'name': 'result',
                            'schema': {'type': 'array'}
                        }
                    }, {
                        'name': 'get_distance',
                        'params': [{
                            'name': 'position',
                            'schema': {
                                '$ref': '#/components/schemas/vector3'
                            },
                            'required': False
                        }, {
                            'name': 'target',
                            'schema': {
                                '$ref': '#/components/schemas/vector3'
                            },
                            'required': False
                        }],
                        'result': {
                            'name': 'result',
                            'schema': {
                                '$ref': '#/components/schemas/vector3'
                            }
                        }
                    }],
                    'components': {
                        'schemas': {
                            'vector3': {
                                'type': 'object',
                                'properties': {
                                    'x': {'type': 'number'},
                                    'y': {'type': 'number'},
                                    'z': {'type': 'number'}
                                }
                            }
                        }
                    }
                }
            }
        )


def increment_list(numbers: list[Union[int, float]]) -> list:
    return [it + 1 for it in numbers]


def get_distance(position: Vector3, target: Vector3) -> Vector3:
    return Vector3(
        position.x - target.x,
        position.y - target.y,
        position.z - target.z,
    )
