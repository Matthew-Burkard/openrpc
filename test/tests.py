import json
import unittest
import uuid

from jsonrpc2.rpc_objects import RPCRequest, RPCResponse
from jsonrpc2.rpc_server import RPCServer

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR = -32000


class RPCTest(unittest.TestCase):

    def __init__(self, *args) -> None:
        self.server = RPCServer()
        self.server.register(add)
        self.server.register(subtract)
        self.server.register(divide)
        self.server.register(summation)
        self.server.register(pythagorean)
        self.server.register(get_none)
        super(RPCTest, self).__init__(*args)

    def test_array_params(self) -> None:
        request = RPCRequest('add', [2, 2], id=1)
        resp = self.server.process(request.to_json())
        self.assertEqual(4, json.loads(resp)['result'])

    def test_no_params(self) -> None:
        request = RPCRequest('get_none', id=1)
        resp = self.server.process(request.to_json())
        self.assertEqual(None, json.loads(resp)['result'])

    def test_object_params(self) -> None:
        request = RPCRequest('subtract', {'x': 2, 'y': 2}, id=1)
        resp = self.server.process(request.to_json())
        self.assertEqual(0, json.loads(resp)['result'])

    def test_vararg_method(self) -> None:
        request = RPCRequest('summation', [1, 3, 5, 7, 11], id=1)
        resp = self.server.process(request.to_json())
        self.assertEqual(27, json.loads(resp)['result'])

    def test_kwarg_method(self) -> None:
        request = RPCRequest('pythagorean', {'a': 3, 'b': 4, 'c': 5}, id=1)
        resp = self.server.process(request.to_json())
        self.assertEqual(True, json.loads(resp)['result'])

    def test_no_result(self) -> None:
        request = RPCRequest('does not exist', id=1)
        resp = self.server.process(request.to_json())
        self.assertNotIn('result', json.loads(resp).keys())
        self.assertIn('error', json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RPCRequest('add', [1, 2], id=1)
        resp = self.server.process(request.to_json())
        self.assertNotIn('error', json.loads(resp).keys())
        self.assertIn('result', json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.server.process(b'}'))
        self.assertEqual(resp['error']['code'], PARSE_ERROR)

    def test_invalid_request(self) -> None:
        resp = json.loads(self.server.process(b'{"id": 1}'))
        self.assertEqual(resp['error']['code'], INVALID_REQUEST)

    def test_method_not_found(self) -> None:
        request = RPCRequest('does not exist', id=1)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], METHOD_NOT_FOUND)

    def test_invalid_params(self) -> None:
        request = RPCRequest('add', {'x': 1, 'z': 2}, id=1)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], INVALID_PARAMS)
        request = RPCRequest('add', [1, 2, 3], id=1)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], INVALID_PARAMS)
        request = RPCRequest('get_none', [1], id=1)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], INVALID_PARAMS)

    def test_internal_error(self) -> None:
        request = RPCRequest('divide', [0, 0], id=1)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], INTERNAL_ERROR)

    def test_server_error(self) -> None:
        uncaught_code = SERVER_ERROR
        request = RPCRequest('divide', [0, 0], id=1)
        server = RPCServer(uncaught_code)
        server.register(divide)
        resp = json.loads(server.process(request.to_json()))
        self.assertEqual(resp['error']['code'], uncaught_code)

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RPCRequest('add', [2, 2], id=req_id)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(4, resp['result'])
        self.assertEqual(req_id, resp['id'])
        # Error id.
        req_id = str(uuid.uuid4())
        request = RPCRequest('add', {'x': 1, 'z': 2}, id=req_id)
        resp = json.loads(self.server.process(request.to_json()))
        self.assertEqual(req_id, resp['id'])

    def test_batch(self) -> None:
        add_id = str(uuid.uuid4())
        subtract_id = str(uuid.uuid4())
        divide_id = str(uuid.uuid4())
        requests = ','.join(
            [
                RPCRequest('add', [2, 2], id=add_id).to_json(),
                RPCRequest('subtract', [2, 2], id=subtract_id).to_json(),
                RPCRequest('divide', [0, 0], id=divide_id).to_json(),
            ]
        )
        responses = json.loads(self.server.process(f'[{requests}]'))
        add_resp = [r for r in responses if r['id'] == add_id][0]
        subtract_resp = [r for r in responses if r['id'] == subtract_id][0]
        divide_resp = [r for r in responses if r['id'] == divide_id][0]
        add_resp = RPCResponse.from_json(json.dumps(add_resp))
        subtract_resp = RPCResponse.from_json(json.dumps(subtract_resp))
        divide_resp = RPCResponse.from_json(json.dumps(divide_resp))
        self.assertEqual(add_id, add_resp.id)
        self.assertEqual(subtract_id, subtract_resp.id)
        self.assertEqual(divide_id, divide_resp.id)
        self.assertEqual(4, add_resp.result)
        self.assertEqual(0, subtract_resp.result)
        self.assertEqual(INTERNAL_ERROR, divide_resp.error.code)


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
