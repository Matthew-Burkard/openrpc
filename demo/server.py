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
