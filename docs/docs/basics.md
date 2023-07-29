---
slug: /basics
sidebar_position: 2
---

# Basics

## Built on Specifications

Python OpenRPC is built on a couple of specifications.

### JSON-RPC 2.0

The [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification) defines the format of
requests and responses of a JSON-RPC server.

### OpenRPC

The [OpenRPC spec](https://open-rpc.org/) defines a document for describing the methods
and schemas used in a JSON-RPC server.

### This Framework

This framework provides a class `RPCServer` that is used to register python functions
as methods in an OpenRPC server.

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
rpc.process_request(req)  # '{"id": 1, "result": 4, "jsonrpc": "2.0"}'
```

## Pydantic For Data Models

For data classes to work properly use [Pydantic](https://docs.pydantic.dev/latest/).
RPCServer will use Pydantic for JSON serialization/deserialization when calling methods
and when generating docs with `rpc.discover`.
