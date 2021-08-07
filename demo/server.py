from dataclasses import dataclass

from openrpc_server import OpenRPCServer

math_rpc = OpenRPCServer('Math RPC Server', '1.0.0', -32000)


@dataclass
class Vector3:
    x: float
    y: float
    z: float


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
def shift(position: Vector3, movement: Vector3) -> Vector3:
    return Vector3(
        position.x + movement.x,
        position.y + movement.y,
        position.z + movement.z,
    )


@math_rpc.method
def get_vector3s(count: int) -> list[Vector3]:
    return [Vector3(1, 1, 1) for _ in range(count)]
