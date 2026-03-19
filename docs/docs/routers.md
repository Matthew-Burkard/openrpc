---
slug: /method-routers
sidebar_position: 5
---

# Method Routers

For larger APIs you may want to organize your methods into different categories with
a common prefix. There's a tool for this in the form of the `AppRouter`. This can be
used to register functions as RPC methods, then the router can be included in an
`RPCApp`. When a router is included in an `RPCApp`, `tags` and/or a `prefix` can
be provided for each method in that router.

```python
from openrpc import AppRouter, RPCApp

rpc = RPCApp()

math_router = AppRouter(prefix="math.", tags=["Math"])
string_router = AppRouter(prefix="string.")


@math_router.method()
def add(a: int, b: int) -> int:
    return a + b


@string_router.method()
def concat(a: str, b: str) -> str:
    return a + b


rpc.include_router(math_router)
rpc.include_router(string_router)

req = '{"id": 1, "method": "math.add", "params": [17, 27], "jsonrpc": "2.0"}'
print(await rpc.process(req))  # {"id":1,"result":44,"jsonrpc":"2.0"}

req = '{"id": 1, "method": "string.concat", "params": ["a", "b"], "jsonrpc": "2.0"}'
print(await rpc.process(req))  # {"id":1,"result":"ab","jsonrpc":"2.0"}
```
