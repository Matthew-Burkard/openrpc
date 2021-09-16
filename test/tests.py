import json
import unittest
import uuid
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Union, Optional

from jsonrpcobjects.errors import JSONRPCError
from jsonrpcobjects.objects import (
    RequestObjectParams,
    RequestObject,
    ErrorObject,
    ErrorObjectData,
    ErrorResponseObject,
    ResultResponseObject,
    ResponseType,
    NotificationObjectParams,
)

from openrpc.objects import MethodObject
from openrpc.server import OpenRPCServer

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR = -32000


class RPCTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.server = OpenRPCServer('Test JSON RPC', '1.0.0')
        self.server.method(increment_list)
        self.server.method(add)
        self.server.method(subtract)
        self.server.method(divide)
        self.server.method(summation)
        self.server.method(pythagorean)
        self.server.method(get_none)
        self.server.method(optional_params)
        self.server.method(args_and_kwargs)
        self.server.method(default_values)
        super(RPCTest, self).__init__(*args)

    def test_array_params(self) -> None:
        request = RequestObjectParams(id=1, method='add', params=[2, 2])
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(4, json.loads(resp)['result'])

    def test_no_params(self) -> None:
        request = RequestObject(id=1, method='get_none')
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(None, json.loads(resp)['result'])

    def test_object_params(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='subtract',
            params={'x': 2, 'y': 2}
        )
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(0, json.loads(resp)['result'])

    def test_vararg_method(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='summation',
            params=[1, 3, 5, 7, 11]
        )
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(27, json.loads(resp)['result'])

    def test_kwarg_method(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='pythagorean',
            params={'a': 3, 'b': 4, 'c': 5}
        )
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(True, json.loads(resp)['result'])

    def test_vararg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method='args_and_kwargs')
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual([{}], json.loads(resp)['result'])

    def test_kwarg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method='args_and_kwargs')
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual([{}], json.loads(resp)['result'])

    def test_no_result(self) -> None:
        request = RequestObjectParams(id=1, method='does not exist', params=[])
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertNotIn('result', json.loads(resp).keys())
        self.assertIn('error', json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RequestObjectParams(id=1, method='add', params=[1, 2])
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertNotIn('error', json.loads(resp).keys())
        self.assertIn('result', json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.server.process_request(b'}'))
        self.assertEqual(resp['error']['code'], PARSE_ERROR)

    def test_invalid_request(self) -> None:
        resp = json.loads(self.server.process_request(b'{"id": 1}'))
        self.assertEqual(resp['error']['code'], INVALID_REQUEST)

    def test_method_not_found(self) -> None:
        request = RequestObject(id=1, method='does not exist')
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['error']['code'], METHOD_NOT_FOUND)

    def test_internal_error(self) -> None:
        request = RequestObjectParams(id=1, method='divide', params=[0, 0])
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['error']['code'], INTERNAL_ERROR)

    def test_server_error(self) -> None:
        uncaught_code = SERVER_ERROR
        request = RequestObjectParams(id=1, method='divide', params=[0, 0])
        server = OpenRPCServer('Test JSON RPC', '1.0.0', uncaught_code)
        server.method(divide)
        resp = json.loads(
            server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['error']['code'], uncaught_code)

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method='add', params=[2, 2])
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(4, resp['result'])
        self.assertEqual(req_id, resp['id'])
        # Error id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(
            id=req_id,
            method='add',
            params={'x': 1, 'z': 2}
        )
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(req_id, resp['id'])

    def test_batch(self) -> None:
        add_id = str(uuid.uuid4())
        subtract_id = str(uuid.uuid4())
        divide_id = str(uuid.uuid4())
        requests = ','.join(
            [
                RequestObjectParams(
                    id=add_id,
                    method='add',
                    params=[2, 2]
                ).json(),
                RequestObjectParams(
                    id=subtract_id,
                    method='subtract',
                    params=[2, 2]
                ).json(),
                RequestObjectParams(
                    id=divide_id,
                    method='divide',
                    params=[0, 0]
                ).json(),
                NotificationObjectParams(method='add', params=[1, 3]).json(),
            ]
        )
        responses = json.loads(self.server.process_request(f'[{requests}]'))
        add_resp = [r for r in responses if r['id'] == add_id][0]
        subtract_resp = [r for r in responses if r['id'] == subtract_id][0]
        divide_resp = [r for r in responses if r['id'] == divide_id][0]
        add_resp = parse_response(json.dumps(add_resp))
        subtract_resp = parse_response(json.dumps(subtract_resp))
        divide_resp = parse_response(json.dumps(divide_resp))
        self.assertEqual(add_id, add_resp.id)
        self.assertEqual(subtract_id, subtract_resp.id)
        self.assertEqual(divide_id, divide_resp.id)
        self.assertEqual(4, add_resp.result)
        self.assertEqual(0, subtract_resp.result)
        self.assertEqual(INTERNAL_ERROR, divide_resp.error.code)
        self.assertEqual(len(responses), 3)

    def test_list_param(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='increment_list',
            params=[[1, 2, 3]]
        )
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['result'], [2, 3, 4])

    def test_optional_params(self) -> None:
        req_id = str(uuid.uuid4())
        # No params.
        req = RequestObject(id=req_id, method='optional_params')
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        self.assertEqual(resp['result'], [None, None])
        # With params.
        req = RequestObjectParams(
            id=req_id,
            method='optional_params',
            params=['three', 3]
        )
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        self.assertEqual(resp['result'], ['three', 3])

    def test_including_method_object(self) -> None:
        def multiply(a: int, b: int) -> int:
            return a * b

        self.server.method(method=MethodObject())(multiply)
        req = RequestObjectParams(id=1, method='multiply', params=[2, 4])
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        self.assertEqual(resp['result'], 8)

    def test_default_values(self) -> None:
        # No params.
        req = RequestObject(id=1, method='default_values')
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        self.assertEqual(resp['result'], 2)
        # First param.
        req = RequestObjectParams(id=1, method='default_values', params=[2])
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        # Both params.
        self.assertEqual(resp['result'], 3)
        req = RequestObjectParams(id=1, method='default_values', params=[2, 2])
        resp = json.loads(
            self.server.process_request(req.json(by_alias=True))
        )
        self.assertEqual(resp['result'], 4)

    def test_json_rpc(self) -> None:
        # Result object.
        request = RequestObjectParams(id=1, method='add', params=[1, 2])
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['jsonrpc'], '2.0')
        # Error object.
        request = RequestObjectParams(id=1, method='divide', params=[0, 0])
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(resp['jsonrpc'], '2.0')

    def test_notifications(self) -> None:
        request = NotificationObjectParams(method='add', params=[1, 2])
        resp = self.server.process_request(request.json(by_alias=True))
        self.assertEqual(None, resp)


def increment_list(numbers: list[Union[int, float]]) -> list:
    return [it + 1 for it in numbers]


def pythagorean(**kwargs) -> bool:
    return (kwargs['a'] ** 2 + kwargs['b'] ** 2) == (kwargs['c'] ** 2)


def summation(*args) -> float:
    return sum(args)


def add(x: float, y: float) -> float:
    return x + y


def subtract(x: float, y: float) -> float:
    return x - y


def divide(x: float, y: float) -> float:
    return x / y


def get_none() -> None:
    return None


def default_values(a: int = 1, b: Optional[int] = None) -> int:
    return a + (b or 1)


def optional_params(
        opt_str: Optional[str] = None,
        opt_int: Optional[int] = None
) -> list:
    return [opt_str, opt_int]


def args_and_kwargs(*args, **kwargs) -> Any:
    return *args, {**kwargs}


########################################################################
# OpenRPC Tests
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
        self.server.method(return_none)
        super(OpenRPCTest, self).__init__(*args)

    def test_open_rpc(self) -> None:
        request = RequestObject(id=1, method='rpc.discover')
        resp = json.loads(
            self.server.process_request(request.json(by_alias=True))
        )
        self.assertEqual(
            resp['result'],
            {
                'openrpc': '1.2.6',
                'info': {'title': 'Open RPC Test Server', 'version': '1.0.0'},
                'methods': [
                    {
                        'name': 'increment',
                        'params': [{
                            'name': 'numbers',
                            'schema': {
                                'type': 'array', 'items': {'type': None}
                            },
                            'required': True
                        }],
                        'result': {
                            'name': 'result',
                            'schema': {
                                'type': 'array', 'items': {'type': None}
                            },
                            'required': True
                        }
                    }, {
                        'name': 'get_distance',
                        'params': [{
                            'name': 'position',
                            'schema': {'$ref': '#/components/schemas/Vector3'},
                            'required': True
                        }, {
                            'name': 'target',
                            'schema': {'$ref': '#/components/schemas/Vector3'},
                            'required': True
                        }],
                        'result': {
                            'name': 'result',
                            'schema': {'$ref': '#/components/schemas/Vector3'},
                            'required': True
                        }
                    }, {
                        'name': 'return_none',
                        'params': [{
                            'name': 'optional_param',
                            'schema': {
                                'anyOf': [{'type': 'string'}, {'type': 'null'}]
                            },
                            'required': False
                        }],
                        'result': {
                            'name': 'result', 'schema': {'type': 'null'},
                            'required': True
                        }
                    }
                ],
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


# noinspection PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:
    return None


def parse_response(data: Union[bytes, str]) -> ResponseType:
    try:
        resp = json.loads(data)
        if resp.get('error'):
            error_resp = ErrorResponseObject(**resp)
            if resp['error'].get('data'):
                error_resp.error = ErrorObjectData(**resp['error'])
            else:
                error_resp.error = ErrorObject(**resp['error'])
            return error_resp
        if 'result' in resp.keys():
            return ResultResponseObject(**resp)
        raise JSONRPCError(
            ErrorObject(
                code=-32000,
                message='Unable to parse response.'
            )
        )
    except (JSONDecodeError, TypeError, AttributeError):
        raise JSONRPCError(
            ErrorObject(
                code=-32000,
                message='Unable to parse response.'
            )
        )
