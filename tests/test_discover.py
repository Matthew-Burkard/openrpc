"""Test the generated "rpc.discover" method."""
import json
import unittest
from typing import Any, Optional, Union

from jsonrpcobjects.objects import RequestObject

from openrpc.objects import ContactObject, LicenseObject
from openrpc.server import RPCServer
from tests.util import Vector3


class OpenRPCTest(unittest.TestCase):
    def __init__(self, *args) -> None:
        self.rpc = RPCServer(title="Test OpenRPC", version="1.0.0")
        self.rpc.method(increment)
        self.rpc.method(get_distance)
        self.rpc.method(return_none)
        self.rpc.method(default_value)
        self.rpc.method(take_any_get_any)
        self.rpc.title = self.rpc.title or "Test OpenRPC"
        self.rpc.version = self.rpc.version or "1.0.0"
        self.rpc.description = self.rpc.description or "Testing rpc.discover"
        self.rpc.terms_of_service = self.rpc.terms_of_service or "Coffee"
        self.rpc.contact = self.rpc.contact or ContactObject(name="mocha")
        self.rpc.license = self.rpc.license or LicenseObject(name="AGPLv3")
        request = RequestObject(id=1, method="rpc.discover")
        resp = json.loads(self.rpc.process_request(request.json()))
        self.discover_result = resp["result"]
        super(OpenRPCTest, self).__init__(*args)

    def test_open_rpc(self) -> None:
        self.assertEqual("1.2.6", self.discover_result["openrpc"])
        self.assertEqual(
            {
                "title": "Test OpenRPC",
                "version": "1.0.0",
                "description": "Testing rpc.discover",
                "termsOfService": "Coffee",
                "contact": {"name": "mocha"},
                "license": {"name": "AGPLv3"},
            },
            self.discover_result["info"]
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
                        "schema": {"type": "integer"},
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


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def increment(numbers: list[Union[int, float]]) -> list[Union[int, str]]:
    pass


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def get_distance(position: Vector3, target: Vector3) -> Vector3:
    pass


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def default_value(a: int = 2, b: float = 0.99792458, c: str = "c") -> str:
    pass


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def return_none(optional_param: Optional[str]) -> None:
    pass


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
def take_any_get_any(any_param: Any) -> Any:
    pass