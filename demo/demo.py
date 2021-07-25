from client import MathRPCClient
from openrpc.exceptions import JSONRPCError
from server import math_rpc

math_rpc_client = MathRPCClient(math_rpc)

print(math_rpc_client.add(4, 5))
try:
    print(math_rpc_client.discover())
    # print(math_rpc_client.divide(0, 0))
except JSONRPCError as e:
    print(e)
