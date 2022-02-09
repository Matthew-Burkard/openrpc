"""Asynchronous OpenRPC tests."""
import asyncio
import json
import unittest
import uuid
from typing import Any, Optional, Union

from jsonrpcobjects.objects import (
    NotificationObject,
    NotificationObjectParams,
    NotificationType,
    RequestObject,
    RequestObjectParams,
    RequestType,
)
from pydantic import BaseModel

from openrpc.objects import InfoObject
from openrpc.server import RPCServer
from tests.util import (
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    parse_response,
    SERVER_ERROR,
    Vector3,
)


# noinspection PyMissingOrEmptyDocstring
class RPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test JSON RPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        self.server.method(add)
        self.server.method(subtract)
        self.server.method(divide)
        self.server.method(args_and_kwargs)
        self.server.method(return_none)
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

    def test_array_params(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[2, 2])
        resp = self.get_result_async(request.json())
        self.assertEqual(4, json.loads(resp)["result"])

    def test_no_params(self) -> None:
        async def get_none() -> None:
            return None

        self.server.method(get_none)
        request = RequestObject(id=1, method="get_none")
        resp = self.get_result_async(request.json())
        self.assertEqual(None, json.loads(resp)["result"])

    def test_object_params(self) -> None:
        request = RequestObjectParams(id=1, method="subtract", params={"x": 2, "y": 2})
        resp = self.get_result_async(request.json())
        self.assertEqual(0, json.loads(resp)["result"])

    def test_vararg_method(self) -> None:
        async def summation(*args) -> float:
            return sum(args)

        self.server.method(summation)
        request = RequestObjectParams(id=1, method="summation", params=[1, 3, 5, 7, 11])
        resp = self.get_result_async(request.json())
        self.assertEqual(27, json.loads(resp)["result"])

    def test_kwarg_method(self) -> None:
        async def pythagorean(**kwargs) -> bool:
            return (kwargs["a"] ** 2 + kwargs["b"] ** 2) == (kwargs["c"] ** 2)

        self.server.method(pythagorean)
        request = RequestObjectParams(
            id=1, method="pythagorean", params={"a": 3, "b": 4, "c": 5}
        )
        resp = self.get_result_async(request.json())
        self.assertEqual(True, json.loads(resp)["result"])

    def test_vararg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.get_result_async(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    def test_kwarg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.get_result_async(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    def test_no_result(self) -> None:
        request = RequestObjectParams(id=1, method="does not exist", params=[])
        resp = self.get_result_async(request.json())
        self.assertNotIn("result", json.loads(resp).keys())
        self.assertIn("error", json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = self.get_result_async(request.json())
        self.assertNotIn("error", json.loads(resp).keys())
        self.assertIn("result", json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.get_result_async(b"}"))
        self.assertEqual(PARSE_ERROR, resp["error"]["code"])

    def test_invalid_request(self) -> None:
        resp = json.loads(self.get_result_async(b'{"id": 1}'))
        self.assertEqual(INVALID_REQUEST, resp["error"]["code"])

    def test_method_not_found(self) -> None:
        request = RequestObject(id=1, method="does not exist")
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual(METHOD_NOT_FOUND, resp["error"]["code"])

    def test_server_error(self) -> None:
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        server = RPCServer(**self.info.dict())
        server.default_error_code = SERVER_ERROR
        server.method(divide)
        resp = json.loads(get_result_async(server, request))
        self.assertEqual(SERVER_ERROR, resp["error"]["code"])

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params=[2, 2])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual(4, resp["result"])
        self.assertEqual(req_id, resp["id"])
        # Error id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params={"x": 1, "z": 2})
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual(req_id, resp["id"])

    # noinspection DuplicatedCode
    def test_batch(self) -> None:
        add_id = str(uuid.uuid4())
        subtract_id = str(uuid.uuid4())
        divide_id = str(uuid.uuid4())
        none_id = str(uuid.uuid4())
        requests = ",".join(
            [
                RequestObjectParams(id=add_id, method="add", params=[2, 2]).json(),
                RequestObjectParams(
                    id=subtract_id, method="subtract", params=[2, 2]
                ).json(),
                RequestObjectParams(
                    id=divide_id, method="divide", params=[0, 0]
                ).json(),
                NotificationObjectParams(method="add", params=[1, 3]).json(),
                '{"fail": "to parse", "as": "jsonrpc request"}',
                NotificationObject(method="does_not_exist").json(),
                RequestObject(id=1, method="does_not_exist").json(),
                NotificationObjectParams(method="divide", params=[0, 0]).json(),
                RequestObject(id=none_id, method="return_none").json(),
            ]
        )
        responses = json.loads(self.get_result_async(f"[{requests}]"))
        add_resp = [r for r in responses if r.get("id") == add_id][0]
        subtract_resp = [r for r in responses if r.get("id") == subtract_id][0]
        divide_resp = [r for r in responses if r.get("id") == divide_id][0]
        none_resp = [r for r in responses if r.get("id") == none_id][0]
        add_resp = parse_response(json.dumps(add_resp))
        subtract_resp = parse_response(json.dumps(subtract_resp))
        divide_resp = parse_response(json.dumps(divide_resp))
        none_resp = parse_response(json.dumps(none_resp))
        self.assertEqual(add_id, add_resp.id)
        self.assertEqual(subtract_id, subtract_resp.id)
        self.assertEqual(divide_id, divide_resp.id)
        self.assertEqual(4, add_resp.result)
        self.assertEqual(0, subtract_resp.result)
        self.assertEqual(SERVER_ERROR, divide_resp.error.code)
        self.assertIsNone(none_resp.result)
        self.assertEqual(len(responses), 6)

    def test_list_param(self) -> None:
        async def increment_list(numbers: list[Union[int, float]]) -> list:
            return [it + 1 for it in numbers]

        self.server.method(increment_list)
        request = RequestObjectParams(id=1, method="increment_list", params=[[1, 2, 3]])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual([2, 3, 4], resp["result"])

    def test_list_object_list_param(self) -> None:
        async def get_vectors(vector3s: list[Vector3]) -> list[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert that the response has a result.
            self.assertEqual(vectors, vector3s)
            return vector3s

        vectors = [Vector3(x=0, y=0, z=0), Vector3(x=1, y=1, z=1)]
        self.server.method(get_vectors)
        request = RequestObjectParams(id=1, method="get_vectors", params=[vectors])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_optional_params(self) -> None:
        async def optional_params(
            opt_str: Optional[str] = None, opt_int: Optional[int] = None
        ) -> list[Union[int, str]]:
            return [opt_str, opt_int]

        self.server.method(optional_params)
        req_id = str(uuid.uuid4())
        # No params.
        req = RequestObject(id=req_id, method="optional_params")
        resp = json.loads(self.get_result_async(req.json()))
        self.assertEqual([None, None], resp["result"])
        # With params.
        req = RequestObjectParams(
            id=req_id, method="optional_params", params=["three", 3]
        )
        resp = json.loads(self.get_result_async(req.json()))
        self.assertEqual(["three", 3], resp["result"])

    def test_optional_object_param(self) -> None:
        vector = Vector3(x=1, y=3, z=5)

        async def optional_param(v: Optional[Vector3] = None) -> Optional[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert the response has a result.
            self.assertEqual(v, vector)
            return v

        self.server.method(optional_param)
        request = RequestObjectParams(id=1, method="optional_param", params=[vector])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_including_method_name(self) -> None:
        async def multiply(a: int, b: int) -> int:
            return a * b

        self.server.method(multiply, name="math.multiply")
        req = RequestObjectParams(id=1, method="math.multiply", params=[2, 4])
        resp = json.loads(self.get_result_async(req.json()))
        self.assertEqual(8, resp["result"])

    def test_default_values(self) -> None:
        async def default_values(a: int = 1, b: Optional[int] = None) -> int:
            return a + (b or 1)

        self.server.method(default_values)
        # No params.
        req = RequestObject(id=1, method="default_values")
        resp = json.loads(self.get_result_async(req.json()))
        self.assertEqual(2, resp["result"])
        # First param.
        req = RequestObjectParams(id=1, method="default_values", params=[2])
        resp = json.loads(self.get_result_async(req.json()))
        # Both params.
        self.assertEqual(3, resp["result"])
        req = RequestObjectParams(id=1, method="default_values", params=[2, 2])
        resp = json.loads(self.get_result_async(req.json()))
        self.assertEqual(4, resp["result"])

    def test_json_rpc(self) -> None:
        # Result object.
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])
        # Error object.
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        resp = json.loads(self.get_result_async(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])

    def test_notifications(self) -> None:
        request = NotificationObjectParams(method="add", params=[1, 2])
        resp = self.get_result_async(request.json())
        self.assertEqual(None, resp)

    def test_deserialize_nested_objects(self) -> None:
        # noinspection PyMissingOrEmptyDocstring
        class Thing(BaseModel):
            name: str
            position: Vector3
            another_thing: Optional["Thing"] = None

        Thing.update_forward_refs()

        async def take_thing(thing: Thing) -> bool:
            self.assertTrue(isinstance(thing, Thing))
            self.assertTrue(isinstance(thing.another_thing, Thing))
            self.assertTrue(isinstance(thing.another_thing.position, Vector3))
            return True

        # noinspection DuplicatedCode
        self.server.method(take_thing)
        req = RequestObjectParams(
            id=1,
            method="take_thing",
            params=[
                Thing(
                    name="ping",
                    position=Vector3(x=1, y=3, z=5),
                    another_thing=Thing(name="pong", position=Vector3(x=7, y=11, z=13)),
                )
            ],
        )
        resp = json.loads(self.get_result_async(req.json()))
        self.assertTrue(resp["result"])

    def test_return_none(self) -> None:
        req = RequestObject(id=1, method="return_none")
        resp = json.loads(self.get_result_async(req.json()))
        self.assertIsNone(resp["result"])


# noinspection PyMissingOrEmptyDocstring
async def add(x: float, y: float) -> float:
    return x + y


# noinspection PyMissingOrEmptyDocstring
async def subtract(x: float, y: float) -> float:
    return x - y


# noinspection PyMissingOrEmptyDocstring
async def divide(x: float, y: float) -> float:
    return x / y


# noinspection PyMissingOrEmptyDocstring
async def args_and_kwargs(*args, **kwargs) -> Any:
    return *args, {**kwargs}


# noinspection PyMissingOrEmptyDocstring
async def return_none() -> None:
    return None


# noinspection PyMissingOrEmptyDocstring
def get_result_async(
    server: RPCServer, request: Union[NotificationType, RequestType]
) -> Optional[str]:
    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server.process_request_async(request.json()))
    loop.close()
    return resp
