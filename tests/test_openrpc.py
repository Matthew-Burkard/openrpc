"""Synchronous OpenRPC tests."""
import json
import unittest
import uuid
from typing import Any, Optional, Union

from jsonrpcobjects.objects import (
    NotificationObjectParams,
    RequestObject,
    RequestObjectParams,
)
from pydantic import BaseModel

from openrpc.objects import InfoObject, MethodObject
from openrpc.server import RPCServer
from tests.util import parse_response

INTERNAL_ERROR = -32603
INVALID_PARAMS = -32602
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
PARSE_ERROR = -32700
SERVER_ERROR = -32000


class Vector3(BaseModel):
    """x, y, and z values."""

    x: float
    y: float
    z: float


# noinspection PyMissingOrEmptyDocstring
class RPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test JSON RPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        self.server.method(add)
        self.server.method(subtract)
        self.server.method(divide)
        self.server.method(args_and_kwargs)
        super(RPCTest, self).__init__(*args)

    def test_array_params(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[2, 2])
        resp = self.server.process_request(request.json())
        self.assertEqual(4, json.loads(resp)["result"])

    def test_no_params(self) -> None:
        def get_none() -> None:
            return None

        self.server.method(get_none)
        request = RequestObject(id=1, method="get_none")
        resp = self.server.process_request(request.json())
        self.assertEqual(None, json.loads(resp)["result"])

    def test_object_params(self) -> None:
        request = RequestObjectParams(id=1, method="subtract", params={"x": 2, "y": 2})
        resp = self.server.process_request(request.json())
        self.assertEqual(0, json.loads(resp)["result"])

    def test_vararg_method(self) -> None:
        def summation(*args) -> float:
            return sum(args)

        self.server.method(summation)
        request = RequestObjectParams(id=1, method="summation", params=[1, 3, 5, 7, 11])
        resp = self.server.process_request(request.json())
        self.assertEqual(27, json.loads(resp)["result"])

    def test_kwarg_method(self) -> None:
        def pythagorean(**kwargs) -> bool:
            return (kwargs["a"] ** 2 + kwargs["b"] ** 2) == (kwargs["c"] ** 2)

        self.server.method(pythagorean)
        request = RequestObjectParams(
            id=1, method="pythagorean", params={"a": 3, "b": 4, "c": 5}
        )
        resp = self.server.process_request(request.json())
        self.assertEqual(True, json.loads(resp)["result"])

    def test_vararg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.server.process_request(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    def test_kwarg_method_with_no_params(self) -> None:
        request = RequestObject(id=1, method="args_and_kwargs")
        resp = self.server.process_request(request.json())
        self.assertEqual([{}], json.loads(resp)["result"])

    def test_no_result(self) -> None:
        request = RequestObjectParams(id=1, method="does not exist", params=[])
        resp = self.server.process_request(request.json())
        self.assertNotIn("result", json.loads(resp).keys())
        self.assertIn("error", json.loads(resp).keys())

    def test_no_error(self) -> None:
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = self.server.process_request(request.json())
        self.assertNotIn("error", json.loads(resp).keys())
        self.assertIn("result", json.loads(resp).keys())

    def test_parse_error(self) -> None:
        resp = json.loads(self.server.process_request(b"}"))
        self.assertEqual(PARSE_ERROR, resp["error"]["code"])

    def test_invalid_request(self) -> None:
        resp = json.loads(self.server.process_request(b'{"id": 1}'))
        self.assertEqual(INVALID_REQUEST, resp["error"]["code"])

    def test_method_not_found(self) -> None:
        request = RequestObject(id=1, method="does not exist")
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual(METHOD_NOT_FOUND, resp["error"]["code"])

    def test_server_error(self) -> None:
        uncaught_code = SERVER_ERROR
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        server = RPCServer(title="Test JSON RPC", version="1.0.0")
        server.default_error_code = uncaught_code
        server.method(divide)
        resp = json.loads(server.process_request(request.json()))
        self.assertEqual(uncaught_code, resp["error"]["code"])

    def test_id_matching(self) -> None:
        # Result id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params=[2, 2])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual(4, resp["result"])
        self.assertEqual(req_id, resp["id"])
        # Error id.
        req_id = str(uuid.uuid4())
        request = RequestObjectParams(id=req_id, method="add", params={"x": 1, "z": 2})
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual(req_id, resp["id"])

    # noinspection DuplicatedCode
    def test_batch(self) -> None:
        add_id = str(uuid.uuid4())
        subtract_id = str(uuid.uuid4())
        divide_id = str(uuid.uuid4())
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
            ]
        )
        responses = json.loads(self.server.process_request(f"[{requests}]"))
        add_resp = [r for r in responses if r["id"] == add_id][0]
        subtract_resp = [r for r in responses if r["id"] == subtract_id][0]
        divide_resp = [r for r in responses if r["id"] == divide_id][0]
        add_resp = parse_response(json.dumps(add_resp))
        subtract_resp = parse_response(json.dumps(subtract_resp))
        divide_resp = parse_response(json.dumps(divide_resp))
        self.assertEqual(add_id, add_resp.id)
        self.assertEqual(subtract_id, subtract_resp.id)
        self.assertEqual(divide_id, divide_resp.id)
        self.assertEqual(4, add_resp.result)
        self.assertEqual(0, subtract_resp.result)
        self.assertEqual(SERVER_ERROR, divide_resp.error.code)
        self.assertEqual(len(responses), 3)

    def test_list_param(self) -> None:
        def increment_list(numbers: list[Union[int, float]]) -> list:
            return [it + 1 for it in numbers]

        self.server.method(increment_list)
        request = RequestObjectParams(id=1, method="increment_list", params=[[1, 2, 3]])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual([2, 3, 4], resp["result"])

    def test_list_object_list_param(self) -> None:
        def get_vectors(vector3s: list[Vector3]) -> list[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert the response has a result.
            self.assertEqual(vectors, vector3s)
            return vector3s

        vectors = [Vector3(x=0, y=0, z=0), Vector3(x=1, y=1, z=1)]
        self.server.method(get_vectors)
        request = RequestObjectParams(id=1, method="get_vectors", params=[vectors])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_optional_params(self) -> None:
        def optional_params(
            opt_str: Optional[str] = None, opt_int: Optional[int] = None
        ) -> list[Union[int, str]]:
            return [opt_str, opt_int]

        self.server.method(optional_params)
        req_id = str(uuid.uuid4())
        # No params.
        req = RequestObject(id=req_id, method="optional_params")
        resp = json.loads(self.server.process_request(req.json()))
        self.assertEqual([None, None], resp["result"])
        # With params.
        req = RequestObjectParams(
            id=req_id, method="optional_params", params=["three", 3]
        )
        resp = json.loads(self.server.process_request(req.json()))
        self.assertEqual(["three", 3], resp["result"])

    def test_optional_object_param(self) -> None:
        vector = Vector3(x=1, y=3, z=5)

        def optional_param(v: Optional[Vector3] = None) -> Optional[Vector3]:
            # This assertion won't fail test if it fails, that's why we
            # assert the response has a result.
            self.assertEqual(v, vector)
            return v

        self.server.method(optional_param)
        request = RequestObjectParams(id=1, method="optional_param", params=[vector])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertIsNotNone(resp.get("result"))

    def test_including_method_name(self) -> None:
        def multiply(a: int, b: int) -> int:
            return a * b

        self.server.method(func=multiply, name="math.multiply")
        req = RequestObjectParams(id=1, method="math.multiply", params=[2, 4])
        resp = json.loads(self.server.process_request(req.json()))
        self.assertEqual(8, resp["result"])

    def test_default_values(self) -> None:
        def default_values(a: int = 1, b: Optional[int] = None) -> int:
            return a + (b or 1)

        self.server.method(default_values)
        # No params.
        req = RequestObject(id=1, method="default_values")
        resp = json.loads(self.server.process_request(req.json()))
        self.assertEqual(2, resp["result"])
        # First param.
        req = RequestObjectParams(id=1, method="default_values", params=[2])
        resp = json.loads(self.server.process_request(req.json()))
        # Both params.
        self.assertEqual(3, resp["result"])
        req = RequestObjectParams(id=1, method="default_values", params=[2, 2])
        resp = json.loads(self.server.process_request(req.json()))
        self.assertEqual(4, resp["result"])

    def test_json_rpc(self) -> None:
        # Result object.
        request = RequestObjectParams(id=1, method="add", params=[1, 2])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])
        # Error object.
        request = RequestObjectParams(id=1, method="divide", params=[0, 0])
        resp = json.loads(self.server.process_request(request.json()))
        self.assertEqual("2.0", resp["jsonrpc"])

    def test_notifications(self) -> None:
        request = NotificationObjectParams(method="add", params=[1, 2])
        resp = self.server.process_request(request.json())
        self.assertEqual(None, resp)

    def test_deserialize_nested_objects(self) -> None:
        # noinspection PyMissingOrEmptyDocstring
        class Thing(BaseModel):
            name: str
            position: Vector3
            another_thing: Optional["Thing"] = None

        Thing.update_forward_refs()

        def take_thing(thing: Thing) -> bool:
            self.assertTrue(isinstance(thing, Thing))
            self.assertTrue(isinstance(thing.another_thing, Thing))
            self.assertTrue(isinstance(thing.another_thing.position, Vector3))
            return True

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
        resp = json.loads(self.server.process_request(req.json()))
        self.assertTrue(resp["result"])


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


########################################################################
# OpenRPC Tests


class OpenRPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.info = InfoObject(title="Test OpenRPC", version="1.0.0")
        self.server = RPCServer(**self.info.dict())
        self.server.method(increment)
        self.server.method(get_distance)
        self.server.method(return_none)
        self.server.method(default_value)
        self.server.method(take_any_get_any)
        request = RequestObject(id=1, method="rpc.discover")
        resp = json.loads(self.server.process_request(request.json()))
        self.discover_result = resp["result"]
        super(OpenRPCTest, self).__init__(*args)

    def test_open_rpc(self) -> None:
        self.assertEqual("1.2.6", self.discover_result["openrpc"])
        self.assertEqual(
            {"title": "Test OpenRPC", "version": "1.0.0"}, self.discover_result["info"]
        )

    def test_lists(self) -> None:
        method = [
            m for m in self.discover_result["methods"] if m["name"] == "increment"
        ][0]
        self.assertEqual(
            {
                "name": "increment",
                "params": [
                    {
                        "name": "numbers",
                        "schema": {"type": "array", "items": {"type": None}},
                        "required": True,
                    }
                ],
                "result": {
                    "name": "result",
                    "schema": {"type": "array", "items": {"type": None}},
                    "required": True,
                },
            },
            method,
        )

    def test_schema_params(self) -> None:
        method = [
            m for m in self.discover_result["methods"] if m["name"] == "get_distance"
        ][0]
        self.assertEqual(
            {
                "name": "get_distance",
                "params": [
                    {
                        "name": "position",
                        "schema": {"$ref": "#/components/schemas/Vector3"},
                        "required": True,
                    },
                    {
                        "name": "target",
                        "schema": {"$ref": "#/components/schemas/Vector3"},
                        "required": True,
                    },
                ],
                "result": {
                    "name": "result",
                    "schema": {"$ref": "#/components/schemas/Vector3"},
                    "required": True,
                },
            },
            method,
        )

    def test_defaults(self) -> None:
        method = [
            m for m in self.discover_result["methods"] if m["name"] == "default_value"
        ][0]
        self.assertEqual(
            {
                "name": "default_value",
                "params": [
                    {
                        "name": "a",
                        "schema": {"type": "number"},
                        "required": False,
                    },
                    {
                        "name": "b",
                        "schema": {"type": "number"},
                        "required": False,
                    },
                    {
                        "name": "c",
                        "schema": {"type": "string"},
                        "required": False,
                    },
                ],
                "result": {
                    "name": "result",
                    "schema": {"type": "string"},
                    "required": True,
                },
            },
            method,
        )

    def test_return_none(self) -> None:
        method = [
            m for m in self.discover_result["methods"] if m["name"] == "return_none"
        ][0]
        self.assertEqual(
            {
                "name": "return_none",
                "params": [
                    {
                        "name": "optional_param",
                        "schema": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "required": False,
                    }
                ],
                "result": {
                    "name": "result",
                    "schema": {"type": "null"},
                    "required": True,
                },
            },
            method,
        )

    def test_any(self) -> None:
        method = [
            m
            for m in self.discover_result["methods"]
            if m["name"] == "take_any_get_any"
        ][0]
        self.assertEqual(
            {
                "name": "take_any_get_any",
                "params": [{"name": "any_param", "required": True, "schema": {}}],
                "result": {"name": "result", "schema": {}, "required": True},
            },
            method,
        )

    def test_schemas(self) -> None:
        self.assertEqual(
            {
                "Vector3": {
                    "type": "object",
                    "description": "x, y, and z values.",
                    "properties": {
                        "x": {"title": "X", "type": "number"},
                        "y": {"title": "Y", "type": "number"},
                        "z": {"title": "Z", "type": "number"},
                    },
                    "required": ["x", "y", "z"],
                    "title": "Vector3",
                }
            },
            self.discover_result["components"]["schemas"],
        )


# noinspection PyMissingOrEmptyDocstring
def increment(numbers: list[Union[int, float]]) -> list[Union[int, str]]:
    return [it + 1 for it in numbers]


# noinspection PyMissingOrEmptyDocstring
def get_distance(position: Vector3, target: Vector3) -> Vector3:
    return Vector3(
        x=position.x - target.x,
        y=position.y - target.y,
        z=position.z - target.z,
    )


# noinspection PyMissingOrEmptyDocstring
def default_value(a: int = 2, b: float = 0.99792458, c: str = "c") -> str:
    return f"{c}{a + b}^8"


# noinspection PyMissingOrEmptyDocstring
# noinspection PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:
    return None


# noinspection PyMissingOrEmptyDocstring
# noinspection PyUnusedLocal
def take_any_get_any(any_param: Any) -> Any:
    return None
