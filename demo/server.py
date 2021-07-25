from openrpc.rpc_server import RPCServer

math_rpc = RPCServer('Math RPC Server', '1.0.0', -32000)


@math_rpc.method()
def add(x: float, y: float) -> float:
    return x + y


@math_rpc.method()
def subtract(x: float, y: float) -> float:
    return x - y


@math_rpc.method()
def divide(x: float, y: float) -> float:
    return x / y
