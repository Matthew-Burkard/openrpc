---
id: Python OpenRPC
slug: /
sidebar_position: 1
---

## Installation

OpenRPC is on PyPI and can be installed with:

```shell
pip install openrpc
```

```shell
poetry add openrpc
```

## Usage

This library provides an `RPCServer` class that can be used to quickly create an OpenRPC
Server.

```python
from openrpc import RPCServer

rpc = RPCServer(title="Demo Server", version="1.0.0")
```

### Register a function as an RPC Method

To register a method with the RPCServer add the `@rpc.method()` decorator to a function.

```python
@rpc.method()
def add(a: int, b: int) -> int:
    return a + b
```

### Process JSON RPC Request

OpenRPC is transport agnostic. To use it, pass JSON RPC requests as strings or byte
strings to the `process_request` or `process_request_async` method.

The `process_request` will return a JSON RPC response as a string.

```python
req = """
{
  "id": 1,
  "method": "add",
  "params": {"a": 2, "b": 2},
  "jsonrpc": "2.0"
}
"""
await rpc.process_request_async(req)
# returns -> '{"id": 1, "result": 4, "jsonrpc": "2.0"}'
```

### Pydantic Support

For data classes to work properly use Pydantic. RPCServer will use Pydantic for JSON
serialization/deserialization when calling methods and when generating schemas
with `rpc.discover`.

### RPC Discover

The `rpc.discover` method is automatically generated. It relies heavily on type hints.

## Example Using Sanic

A quick example using `OpenRPC` exposing the methods
using a [Sanic](https://sanic.dev/en/) websocket server.

```python
from openrpc import RPCServer
from sanic import Request, Sanic, Websocket

app = Sanic("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


@app.websocket("/api/v1/")
async def process_websocket(_request: Request, ws: Websocket) -> None:
    async for msg in ws:
        json_rpc_response = await rpc.process_request_async(msg)
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)


if __name__ == "__main__":
    app.run()
```

Example In

```json
{
  "id": 1,
  "method": "add",
  "params": {
    "a": 1,
    "b": 3
  },
  "jsonrpc": "2.0"
}
```

Example Result Out

```json
{
  "id": 1,
  "result": 4,
  "jsonrpc": "2.0"
}
```
