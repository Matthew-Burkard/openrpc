import json
import unittest
import uuid
from typing import Any, Union, Optional

from openrpc import util
from openrpc.rpc_objects import RequestObjectParams, RequestObject
from server import OpenRPCServer

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
        self.server.method(echo)
        super(RPCTest, self).__init__(*args)

    def test_array_params(self) -> None:
        request = RequestObjectParams(id=1, method='add', params=[2, 2])
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual(4, json.loads(resp)['result'])

    def test_no_params(self) -> None:
        request = RequestObject(id=1, method='get_none')
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual(None, json.loads(resp)['result'])

    def test_object_params(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='subtract',
            params={'x': 2, 'y': 2}
        )
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual(0, json.loads(resp)['result'])

    def test_vararg_method(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='summation',
            params=[1, 3, 5, 7, 11]
        )
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual(27, json.loads(resp)['result'])

    def test_kwarg_method(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='pythagorean',
            params={'a': 3, 'b': 4, 'c': 5}
        )
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual(True, json.loads(resp)['result'])

    def test_vararg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method='echo')
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual([{}], json.loads(resp)['result'])

    def test_kwarg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method='echo')
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertEqual([{}], json.loads(resp)['result'])

    def test_no_result(self) -> None:
        request = RequestObjectParams(id=1, method='does not exist', params=[])
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertNotIn('result', json.loads(resp).keys())
        self.assertIn('error', json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RequestObjectParams(id=1, method='add', params=[1, 2])
        resp = self.server.process(
            request.json(by_alias=True, exclude_unset=True)
        )
        self.assertNotIn('error', json.loads(resp).keys())
        self.assertIn('result', json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.server.process(b'}'))
        self.assertEqual(resp['error']['code'], PARSE_ERROR)

    def test_invalid_request(self) -> None:
        resp = json.loads(self.server.process(b'{"id": 1}'))
        self.assertEqual(resp['error']['code'], INVALID_REQUEST)

    def test_method_not_found(self) -> None:
        request = RequestObject(id=1, method='does not exist')
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(resp['error']['code'], METHOD_NOT_FOUND)

    def test_internal_error(self) -> None:
        request = RequestObjectParams(id=1, method='divide', params=[0, 0])
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(resp['error']['code'], INTERNAL_ERROR)

    def test_server_error(self) -> None:
        uncaught_code = SERVER_ERROR
        request = RequestObjectParams(id=1, method='divide', params=[0, 0])
        server = OpenRPCServer('Test JSON RPC', '1.0.0', uncaught_code)
        server.method(divide)
        resp = json.loads(
            server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(resp['error']['code'], uncaught_code)

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method='add', params=[2, 2])
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
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
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
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
                ).json(by_alias=True, exclude_unset=True),
                RequestObjectParams(
                    id=subtract_id,
                    method='subtract',
                    params=[2, 2]
                ).json(by_alias=True, exclude_unset=True),
                RequestObjectParams(
                    id=divide_id,
                    method='divide',
                    params=[0, 0]
                ).json(by_alias=True, exclude_unset=True),
            ]
        )
        responses = json.loads(self.server.process(f'[{requests}]'))
        add_resp = [r for r in responses if r['id'] == add_id][0]
        subtract_resp = [r for r in responses if r['id'] == subtract_id][0]
        divide_resp = [r for r in responses if r['id'] == divide_id][0]
        add_resp = util.parse_response(json.dumps(add_resp))
        subtract_resp = util.parse_response(json.dumps(subtract_resp))
        divide_resp = util.parse_response(json.dumps(divide_resp))
        self.assertEqual(add_id, add_resp.id)
        self.assertEqual(subtract_id, subtract_resp.id)
        self.assertEqual(divide_id, divide_resp.id)
        self.assertEqual(4, add_resp.result)
        self.assertEqual(0, subtract_resp.result)
        self.assertEqual(INTERNAL_ERROR, divide_resp.error.code)

    def test_list_param(self) -> None:
        request = RequestObjectParams(
            id=1,
            method='increment_list',
            params=[[1, 2, 3]]
        )
        resp = json.loads(
            self.server.process(
                request.json(by_alias=True, exclude_unset=True)
            )
        )
        self.assertEqual(resp['result'], [2, 3, 4])

    def test_optional_params(self) -> None:
        req_id = str(uuid.uuid4())
        # No params.
        req = RequestObject(id=req_id, method='optional_params')
        resp = json.loads(
            self.server.process(req.json(by_alias=True, exclude_unset=True))
        )
        self.assertEqual(resp['result'], [None, None])
        # With params.
        req = RequestObjectParams(
            id=req_id,
            method='optional_params',
            params=['three', 3]
        )
        resp = json.loads(
            self.server.process(req.json(by_alias=True, exclude_unset=True))
        )
        self.assertEqual(resp['result'], ['three', 3])


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


def optional_params(
        opt_str: Optional[str] = None,
        opt_int: Optional[int] = None
) -> list:
    return [opt_str, opt_int]


def echo(*args, **kwargs) -> Any:
    return *args, {**kwargs}
