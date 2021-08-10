from dataclasses import dataclass
from typing import Union

import pydantic

from server import OpenRPCServer

math_rpc = OpenRPCServer('Math RPC Server', '1.0.0', -32000)


@dataclass
class Vector3(pydantic.BaseModel):
    x: float
    y: float
    z: float


# To test replacing definitions, should be in a real test.
@dataclass
class Vector3Clone(pydantic.BaseModel):
    x: float
    y: float
    z: float


@dataclass
class Model(pydantic.BaseModel):
    name: str
    position: Vector3Clone


@math_rpc.method
def add(x: float, y: float) -> float:
    return x + y


@math_rpc.method
def subtract(x: float, y: float) -> float:
    return x - y


@math_rpc.method
def divide(x: float, y: float) -> float:
    return x / y


@math_rpc.method
def increment_list(numbers: list[Union[int, float]]) -> list:
    return [it + 1 for it in numbers]


@math_rpc.method
def distance(model: Model, target: Vector3) -> Vector3:
    return Vector3(
        model.position.x - target.x,
        model.position.y - target.y,
        model.position.z - target.z,
    )


@math_rpc.method
def get_vector3s(count: int) -> list[Vector3]:
    return [Vector3(1, 1, 1) for _ in range(count)]


@math_rpc.method
def get_vector3_map(count: int) -> dict[str, Vector3]:
    return {f'{i}': Vector3(1, 1, 1) for i in range(count)}
