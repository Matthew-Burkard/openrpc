"""OpenRPC tests."""
from __future__ import annotations

import asyncio
import json
import re
import unittest
import uuid
from typing import Any, Callable, Optional, Union

from jsonrpcobjects.objects import (
    NotificationObject,
    NotificationObjectParams,
    RequestObject,
    RequestObjectParams,
)
from pydantic import BaseModel

from openrpc.objects import InfoObject
from openrpc.server import RPCServer
from tests.util import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    parse_response,
    SERVER_ERROR,
    Vector3,
)


# This needs to be defined at top level for future annotations to work.
# noinspection PyMissingOrEmptyDocstring
class RecursiveModel(BaseModel):
    name: str
    position: Vector3
    another_thing: Optional[RecursiveModel] = None
    another_thing_no_future_annotations: Optional["RecursiveModel"] = None


RecursiveModel.update_forward_refs()


# noinspection PyMissingOrEmptyDocstring
class RPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test JSON RPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        self.method(add)
        self.method(subtract)
        self.method(divide)
        self.method(args_and_kwargs)
        self.method(return_none)
        super(RPCTest, self).__init__(*args)

    def test_array_params(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[2, 2])
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(4, json.loads(resp)["result"])

    def test_no_params(self) -> None:
        def get_none() -> None:
            return None

        self.method(get_none)
        request = RequestObject(id=1, method="get_none")
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(None, json.loads(resp)["result"])

    def test_object_params(self) -> None:
        request = RequestObjectParams(id=1, method="subtract", params={"x": 2, "y": 2})
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(0, json.loads(resp)["result"])

    def test_vararg_method(self) -> None:
        def summation(*args) -> float:
            return sum(args)

        self.method(summation)
        request = RequestObjectParams(id=1, method="summation", params=[1, 3, 5, 7, 11])
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(27, json.loads(resp)["result"])

    def test_kwarg_method(self) -> None:
        def pythagorean(**kwargs) -> bool:
            return (kwargs["a"] ** 2 + kwargs["b"] ** 2) == (kwargs["c"] ** 2)

        self.method(pythagorean)
        request = RequestObjectParams(
            id=1, method="pythagorean", params={"a": 3, "b": 4, "c": 5}
        )
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(True, json.loads(resp)["result"])

    # noinspection DuplicatedCode
    def test_vararg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    # noinspection DuplicatedCode
    def test_kwarg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    def test_no_result(self) -> None:
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        resp = self.get_sync_and_async_resp(request.json())
        self.assertNotIn("result", json.loads(resp).keys())
        self.assertIn("error", json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = self.get_sync_and_async_resp(request.json())
        self.assertNotIn("error", json.loads(resp).keys())
        self.assertIn("result", json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.get_sync_and_async_resp(b"}"))
        self.assertEqual(PARSE_ERROR, resp["error"]["code"])

    def test_invalid_request(self) -> None:
        resp = json.loads(self.get_sync_and_async_resp(b'{"id": 1}'))
        self.assertEqual(INVALID_REQUEST, resp["error"]["code"])

    def test_method_not_found(self) -> None:
        request = RequestObject(id=1, method="does not exist")
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual(METHOD_NOT_FOUND, resp["error"]["code"])

    def test_server_error(self) -> None:
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        server = RPCServer(title="Test JSON RPC", version="1.0.0")
        server.default_error_code = SERVER_ERROR
        server.method(divide)
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual(server.default_error_code, resp["error"]["code"])

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params=[2, 2])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual(4, resp["result"])
        self.assertEqual(req_id, resp["id"])
        # Error id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params={"x": 1, "z": 2})
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
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
                "null",
                NotificationObject(method="does_not_exist").json(),
                NotificationObjectParams(method="divide", params=[0, 0]).json(),
                RequestObject(id=1, method="does_not_exist").json(),
                RequestObject(id=none_id, method="return_none").json(),
            ]
        )
        responses = json.loads(self.get_sync_and_async_resp(f"[{requests}]"))
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
        def increment_list(numbers: list[Union[int, float]]) -> list:
            return [it + 1 for it in numbers]

        self.method(increment_list)
        request = RequestObjectParams(id=1, method="increment_list", params=[[1, 2, 3]])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual([2, 3, 4], resp["result"])

    def test_list_object_list_param(self) -> None:
        def get_vectors(vector3s: list[Vector3]) -> list[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert the response has a result.
            self.assertEqual(vectors, vector3s)
            return vector3s

        vectors = [Vector3(x=0, y=0, z=0), Vector3(x=1, y=1, z=1)]
        self.method(get_vectors)
        request = RequestObjectParams(id=1, method="get_vectors", params=[vectors])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_optional_params(self) -> None:
        def optional_params(
            opt_str: Optional[str] = None, opt_int: Optional[int] = None
        ) -> list[Union[int, str]]:
            return [opt_str, opt_int]

        self.method(optional_params)
        req_id = str(uuid.uuid4())
        # No params.
        req = RequestObject(id=req_id, method="optional_params")
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual([None, None], resp["result"])
        # With params.
        req = RequestObjectParams(
            id=req_id, method="optional_params", params=["three", 3]
        )
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual(["three", 3], resp["result"])

    def test_optional_object_param(self) -> None:
        vector = Vector3(x=1, y=3, z=5)

        def optional_param(v: Optional[Vector3] = None) -> Optional[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert the response has a result.
            self.assertEqual(v, vector)
            return v

        self.method(optional_param)
        request = RequestObjectParams(id=1, method="optional_param", params=[vector])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_including_method_name(self) -> None:
        def multiply(a: int, b: int) -> int:
            return a * b

        self.method(multiply, name="math.multiply")
        req = RequestObjectParams(id=1, method="math.multiply", params=[2, 4])
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual(8, resp["result"])

    def test_default_values(self) -> None:
        def default_values(a: int = 1, b: Optional[int] = None) -> int:
            return a + (b or 1)

        self.method(default_values)
        # No params.
        req = RequestObject(id=1, method="default_values")
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual(2, resp["result"])
        # First param.
        req = RequestObjectParams(id=1, method="default_values", params=[2])
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        # Both params.
        self.assertEqual(3, resp["result"])
        req = RequestObjectParams(id=1, method="default_values", params=[2, 2])
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual(4, resp["result"])

    def test_json_rpc(self) -> None:
        # Result object.
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])
        # Error object.
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        resp = json.loads(self.get_sync_and_async_resp(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])

    def test_notifications(self) -> None:
        request = NotificationObjectParams(method="add", params=[1, 2])
        resp = self.get_sync_and_async_resp(request.json())
        self.assertEqual(None, resp)

    def test_deserialize_nested_objects(self) -> None:
        def take_thing(thing: RecursiveModel) -> bool:
            self.assertTrue(isinstance(thing, RecursiveModel))
            self.assertTrue(isinstance(thing.another_thing, RecursiveModel))
            self.assertTrue(isinstance(thing.another_thing.position, Vector3))
            self.assertTrue(
                isinstance(thing.another_thing_no_future_annotations.position, Vector3)
            )
            return True

        # noinspection DuplicatedCode
        self.method(take_thing)
        req = RequestObjectParams(
            id=1,
            method="take_thing",
            params=[
                RecursiveModel(
                    name="ping",
                    position=Vector3(x=1, y=3, z=5),
                    another_thing=RecursiveModel(
                        name="pong", position=Vector3(x=7, y=11, z=13)
                    ),
                    another_thing_no_future_annotations=RecursiveModel(
                        name="pong", position=Vector3(x=7, y=11, z=13)
                    ),
                )
            ],
        )
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertTrue(resp["result"])

    def test_return_none(self) -> None:
        req = RequestObject(id=1, method="return_none")
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertIsNone(resp["result"])

    def test_catchall_error(self) -> None:
        req = RequestObject(id=1, method="return_none")
        mp = self.server._method_processor
        self.server._method_processor = None
        resp = json.loads(self.get_sync_and_async_resp(req.json()))
        self.assertEqual(INTERNAL_ERROR, resp["code"])
        self.server._method_processor = mp

    def test_no_response_on_method_not_found_notify(self) -> None:
        req = NotificationObject(method="not_a_method")
        resp = self.get_sync_and_async_resp(req.json())
        self.assertIsNone(resp)

    def get_sync_and_async_resp(self, request: Union[str, bytes]) -> str:
        sync_resp = self.server.process_request(request)
        loop = asyncio.new_event_loop()
        if "method" in str(request):
            request = re.sub(r'("method": ?)"(.+?)"', r'\1"async_\2"', request)
        async_resp = loop.run_until_complete(self.server.process_request_async(request))
        loop.close()
        if sync_resp != async_resp:
            async_resp = re.sub(r"_?async_?", "", async_resp)
        self.assertEqual(sync_resp, async_resp)
        return sync_resp

    def method(self, func: Callable, name: Optional[str] = None) -> None:
        self.server.method(func, name=name)
        if name is not None:
            name = f"async_{name}"
        self.server.method(get_as_async(func), name=name)


# noinspection PyUnresolvedReferences
def get_as_async(func: Callable) -> Callable:
    """Get an async version of a function."""

    async def _wrapper(*args, **kwargs) -> Any:
        return func(*args, **kwargs)

    _wrapper.__name__ = f"async_{func.__name__}"
    _wrapper.__annotations__ = func.__annotations__
    return _wrapper


# noinspection PyMissingOrEmptyDocstring
def add(x: float, y: float) -> float:
    return x + y


# noinspection PyMissingOrEmptyDocstring
def subtract(x: float, y: float) -> float:
    return x - y


# noinspection PyMissingOrEmptyDocstring
def divide(x: float, y: float) -> float:
    return x / y


# noinspection PyMissingOrEmptyDocstring
def args_and_kwargs(*args, **kwargs) -> Any:
    return *args, {**kwargs}


# noinspection PyMissingOrEmptyDocstring
def return_none() -> None:
    return None
