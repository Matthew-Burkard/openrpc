from client import MathRPCClient, Vector3
from openrpc.exceptions import JSONRPCError
from server import math_rpc

math_rpc_client = MathRPCClient(math_rpc)

print(math_rpc_client.add(4, 5))
try:
    print(math_rpc_client.discover())
    print(math_rpc_client.shift(Vector3(1, 1, 2), Vector3(3, 4, 1)))
    # print(math_rpc_client.divide(0, 0))
except JSONRPCError as e:
    print(e)
