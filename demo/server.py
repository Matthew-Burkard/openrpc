from jsonrpc2.rpc_server import RPCServer

math_rpc = RPCServer()


@math_rpc.register
def add(x: float, y: float) -> float:
    return x + y


@math_rpc.register
def subtract(x: float, y: float) -> float:
    return x - y


@math_rpc.register
def divide(x: float, y: float) -> float:
    return x / y
