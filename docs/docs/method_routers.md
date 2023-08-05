---
slug: /method_routers
sidebar_position: 3
---

# Method Routers

For larger APIs you may want to organize your methods into different categories with
a common prefix. There's a tool for this in the form of the `RPCRouter`. This can be
used to register functions as RPC methods, then the router can be included in an
`RPCServer` with an optional method name prefix for methods of that router.

```python
from openrpc import RPCRouter, RPCServer

rpc = RPCServer(title="RPCServer", version="1.0.0", debug=True)

math_router = RPCRouter()
string_router = RPCRouter()


@math_router.method()
def add(a: int, b: int) -> int:
    return a + b


@string_router.method()
def concat(a: str, b: str) -> str:
    return a + b


rpc.include_router(math_router, prefix="math.")
rpc.include_router(string_router, prefix="string.")

req = '{"id": 1, "method": "math.add", "params": [17, 27], "jsonrpc": "2.0"}'
print(rpc.process_request(req))  # {"id":1,"result":44,"jsonrpc":"2.0"}

req = '{"id": 1, "method": "string.concat", "params": ["a", "b"], "jsonrpc": "2.0"}'
print(rpc.process_request(req))  # {"id":1,"result":"ab","jsonrpc":"2.0"}
```
