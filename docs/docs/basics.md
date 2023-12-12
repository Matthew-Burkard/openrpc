---
slug: /basics
sidebar_position: 2
---

# Basics

## Built on Specifications

Python OpenRPC is built on multiple specifications.

### JSON-RPC 2.0

The [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification) is a transport agnostic
spec which defines the properties of a JSON-RPC server. A JSON-RPC server will have
methods that can be called remotely. The spec defines the format of requests expected by
a JSON-RPC server to call a method and the format that the server responses must match.

### OpenRPC

The [OpenRPC spec](https://open-rpc.org/) defines a document for describing the methods
and schemas used in a JSON-RPC server. It's like [OpenAPI](https://www.openapis.org/)
for JSON-RPC APIs. The OpenRPC document will list each method in the server along with
the parameters expected by those method and the result it will produce. Like OpenAPI, it
leverages [JSON Schemas](https://json-schema.org/) to describe types.

## What Does This Framework Do?

This framework provides a class, `RPCServer`, that is used to register python functions
as methods in an OpenRPC server. Once methods are registered the framework can parse
JSON-RPC requests, call the appropriate function, wrap the function's return value in
a JSON-RPC response and return it.

### Usage

To register a method with the RPCServer use the `@rpc.method()` decorator on a function.

```python
from openrpc import RPCServer

rpc = RPCServer(title="Demo Server", version="1.0.0")


@rpc.method()
def add(a: int, b: int) -> int:
    return a + b
```

### Process JSON-RPC Request

OpenRPC is transport agnostic. To use it, pass JSON-RPC requests as strings or byte
strings to the `process_request` or `process_request_async` methods.

Calling `process_request` will parse
the [JSON-RPC request](https://www.jsonrpc.org/specification#request_object) and call
the appropriate function based on method name. Then the result of that function will be
wrapped in a [JSON-RPC response](https://www.jsonrpc.org/specification#response_object)
and returned as a string.

```python
req = """
{
  "id": 1,
  "method": "add",
  "params": {"a": 2, "b": 2},
  "jsonrpc": "2.0"
}
"""
rpc.process_request(req)  # '{"id":1,"result":4,"jsonrpc":"2.0"}'
```

## Pydantic For Data Models

For data classes to work properly use [Pydantic](https://docs.pydantic.dev/latest/).
RPCServer will use Pydantic for JSON serialization/deserialization when calling methods
and for schema generation when getting docs with `rpc.discover`.

### Pydantic Example

```python
from openrpc import RPCServer
from pydantic import BaseModel

rpc = RPCServer(title="Demo Server", version="1.0.0")


class Vector3(BaseModel):
    x: float = 1.0
    y: float = 1.0
    z: float = 1.0


@rpc.method()
def get_distance(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(
        x=a.x - b.x,
        y=a.y - b.y,
        z=a.z - b.z,
    )


req = """
{
  "id": 1,
  "method": "get_distance",
  "params": [{"x": 3.0, "y": 5.0, "z": 7.0}, {"x": 1.0, "y": 1.0, "z": 1.0}],
  "jsonrpc": "2.0"
}
"""
rpc.process_request(req)  # '{"id":1,"result":{"x":2.0,"y":4.0,"z":6.0},"jsonrpc":"2.0"}'
```
