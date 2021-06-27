from client import MathRPCClient
from server import math_rpc

math_rpc_client = MathRPCClient(math_rpc)

print(math_rpc_client.add(4, 5))
