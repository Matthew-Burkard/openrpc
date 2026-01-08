"""OpenRPC tests."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional, Union

import pytest
from jsonrpcobjects.objects import Notification
from pydantic import BaseModel

from openrpc import RPCApp
from tests.util import INVALID_REQUEST, METHOD_NOT_FOUND, PARSE_ERROR, Vector3
from tests.v11 import util


# This needs to be defined at top level for future annotations to work.
# noinspection PyMissingOrEmptyDocstring
class RecursiveModel(BaseModel):
    name: str
    position: Vector3
    another_thing: Optional[RecursiveModel] = None
    another_thing_no_future_annotations: Optional["RecursiveModel"] = None


_ = RecursiveModel.model_rebuild()

rpc = RPCApp()


@pytest.mark.asyncio
async def test_array_params() -> None:
    result = await util.get_result(rpc, add, [2, 2])
    expected = 4
    assert result == expected


@pytest.mark.asyncio
async def test_no_params() -> None:
    result = await util.get_result(rpc, get_none)
    assert result is None


@pytest.mark.asyncio
async def test_object_params() -> None:
    result = await util.get_result(rpc, add, {"x": 2, "y": 2})
    expected = 4
    assert result == expected


@pytest.mark.asyncio
async def test_vararg_method_with_no_params() -> None:
    result = await util.get_result(rpc, args_and_kwargs)
    assert result == [{}]


@pytest.mark.asyncio
async def test_no_result() -> None:
    result = await util.get_result(rpc, divide, [0, 0])
    assert "result" not in result
    assert "error" in result


@pytest.mark.asyncio
async def test_no_error() -> None:
    request = util.req_str(add.__name__, [1, 2])
    response = json.loads(await rpc.process(request) or "")
    assert "result" in response
    assert "error" not in response


@pytest.mark.asyncio
async def test_parse_error() -> None:
    result = json.loads(await rpc.process("{]") or "")
    assert result["error"]["code"] == PARSE_ERROR


@pytest.mark.asyncio
async def test_invalid_request() -> None:
    result = json.loads(await rpc.process('{"id": 1}') or "")
    assert result["error"]["code"] == INVALID_REQUEST


@pytest.mark.asyncio
async def test_method_not_found() -> None:
    result = await util.get_result(rpc, "broccoli")
    assert result["error"]["code"] == METHOD_NOT_FOUND


@pytest.mark.asyncio
async def test_id_matching() -> None:
    # Result id.
    req_id = str(uuid.uuid4())
    request = (
        '{"id": "%s", "method": "add", "params": [2, 2], "jsonrpc": "2.0"}' % req_id
    )
    result = json.loads(await rpc.process(request) or "")
    assert req_id == result["id"]
    # Error id.
    req_id = str(uuid.uuid4())
    request = (
        '{"id": "%s", "method": "add", "params": {"z": 1}, "jsonrpc": "2.0"}' % req_id
    )
    result = json.loads(await rpc.process(request) or "")
    assert req_id == result["id"]


@pytest.mark.asyncio
async def test_list_param() -> None:
    def increment_list(  # pyright: ignore[reportUnknownParameterType]
        numbers: list[Union[int, float]],
    ) -> list:  # pyright: ignore[reportMissingTypeArgument]
        return [it + 1 for it in numbers]  # pyright: ignore[reportUnknownVariableType]

    app = util.get_app_with_method(
        increment_list  # pyright: ignore[reportUnknownArgumentType]
    )
    result = await util.get_result(
        app, increment_list, [[1, 2, 3]]  # pyright: ignore[reportUnknownArgumentType]
    )
    expected = [2, 3, 4]
    assert result == expected


@pytest.mark.asyncio
async def test_list_object_list_param() -> None:
    def get_vectors(vector3s: list[Vector3]) -> list[Vector3]:
        # This assertion won't fail test if it fails, that's why we
        # assert the response has a result.
        assert vectors == vector3s
        return vector3s

    vectors = [Vector3(x=0, y=0, z=0), Vector3(x=1, y=1, z=1)]
    app = util.get_app_with_method(get_vectors)
    result = await util.get_result(app, get_vectors, [vectors])
    assert result[1]["x"] == 1


@pytest.mark.asyncio
async def test_optional_params() -> None:
    def optional_params(
        opt_str: Optional[str] = None, opt_int: Optional[int] = None
    ) -> list[Union[int, str]]:
        return [opt_str or "", opt_int or 0]

    app = util.get_app_with_method(optional_params)
    # No params.
    result = await util.get_result(app, optional_params)
    assert result == ["", 0]
    # With params.
    result = await util.get_result(app, optional_params, ["three", 3])
    assert result == ["three", 3]


@pytest.mark.asyncio
async def test_optional_object_param() -> None:
    vector = Vector3(x=1, y=3, z=5)

    def optional_param(v: Optional[Vector3] = None) -> Optional[Vector3]:
        # This assertion won't fail test if it fails, that's why we
        # assert the response has a result.
        assert v == vector
        return v

    app = util.get_app_with_method(optional_param)
    result = await util.get_result(app, optional_param, [vector])
    assert result["z"] == vector.z


@pytest.mark.asyncio
async def test_including_method_name() -> None:
    def multiply(a: int, b: int) -> int:
        return a * b

    app = util.get_app_with_method(multiply, "math.multiply")
    result = await util.get_result(app, "math.multiply", [2, 4])
    assert result == 8  # noqa: PLR2004


@pytest.mark.asyncio
async def test_default_values() -> None:
    def default_values(a: int = 1, b: Optional[int] = None) -> int:
        return a + (b or 1)

    app = util.get_app_with_method(default_values)
    # No params.
    result = await util.get_result(app, default_values)
    assert result == 2  # noqa: PLR2004
    # First param.
    result = await util.get_result(app, default_values, [2])
    assert result == 3  # noqa: PLR2004
    # Both params.
    result = await util.get_result(app, default_values, [2, 2])
    assert result == 4  # noqa: PLR2004


@pytest.mark.asyncio
async def test_json_rpc() -> None:
    # Result object.
    request = util.req_str(add.__name__, [1, 2])
    response = json.loads(await rpc.process(request) or "")
    assert response["jsonrpc"] == "2.0"
    # Error object.
    request = util.req_str(divide.__name__, [1, 0])
    response = json.loads(await rpc.process(request) or "")
    assert response["jsonrpc"] == "2.0"


@pytest.mark.asyncio
async def test_notifications() -> None:
    request = '{"method":"add","params":[1,2],"jsonrpc":"2.0"}'
    response = json.loads(await rpc.process(request) or "null")
    assert response is None


@pytest.mark.asyncio
async def test_deserialize_nested_objects() -> None:
    def take_thing(thing: RecursiveModel) -> bool:
        assert isinstance(thing.another_thing, RecursiveModel)
        assert isinstance(thing.another_thing.position, Vector3)
        assert isinstance(thing.another_thing_no_future_annotations, RecursiveModel)
        assert isinstance(thing.another_thing_no_future_annotations.position, Vector3)
        return True

    app = util.get_app_with_method(take_thing)
    params = [
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
    ]
    result = await util.get_result(app, take_thing, params)
    assert result is True


@pytest.mark.asyncio
async def test_return_none() -> None:
    result = await util.get_result(rpc, return_none)
    assert result is None


@pytest.mark.asyncio
async def test_no_response_on_method_not_found_notify() -> None:
    req = Notification(method="not_a_method")
    response = await rpc.process(req.model_dump_json(by_alias=True)) or None
    assert response is None


@rpc.method()
def add(x: float, y: float) -> float:
    """Add two floats."""
    return x + y


@rpc.method()
def subtract(x: float, y: float) -> float:
    """Subtract two floats."""
    return x - y


@rpc.method()
def divide(x: float, y: float) -> float:
    """Divide two floats."""
    return x / y


@rpc.method()
def args_and_kwargs(*args: Any, **kwargs: Any) -> Any:
    """Function with `*args` and `**kwargs`."""
    return *args, {**kwargs}


@rpc.method()
def return_none() -> None:
    """Function that returns `None`."""
    return


@rpc.method()
def get_none() -> None:
    return None
