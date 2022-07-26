<div align=center>
  <h1>OpenRPC</h1>
  <h3>OpenRPC provides classes to rapidly develop an
  <a href="https://open-rpc.org">OpenRPC</a> server.</h3>
  <img src="https://img.shields.io/badge/License-MIT-blue.svg"
   height="20"
   alt="License: MIT">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg"
   height="20"
   alt="Code style: black">
  <img src="https://img.shields.io/pypi/v/openrpc.svg"
   height="20"
   alt="PyPI version">
  <img src="https://img.shields.io/badge/coverage-100%25-success"
   height="20"
   alt="Code Coverage">
  <a href="https://www.codefactor.io/repository/github/matthew-burkard/openrpc">
    <img src="https://www.codefactor.io/repository/github/matthew-burkard/openrpc/badge" 
     alt="CodeFactor" /></a>
  <a href="https://gitlab.com/mburkard/openrpc/-/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/static/v1.svg?label=Contributions&message=Welcome&color=2267a0"
     height="20"
     alt="Contributions Welcome">
  </a>
</div>

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
from openrpc.server import RPCServer

rpc = RPCServer(title="Demo Server", version="1.0.0")
```

### Register a function as an RPC Method

To register a method with the RPCServer add the `@rpc.method` decorator to a function.

```python
@rpc.method
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
using [Sanic](https://sanic.dev/en/).

```python
from sanic import HTTPResponse, Request, Sanic, text

from openrpc.server import RPCServer

app = Sanic("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method
def add(a: int, b: int) -> int:
    return a + b


@app.post("/api/v1/")
def process_rpc(request: Request) -> HTTPResponse:
    return text(rpc.process_request(request.body))


if __name__ == "__main__":
    app.run()
```

Example In

```json
[
  {
    "id": 1,
    "method": "add",
    "params": {
      "a": 1,
      "b": 3
    },
    "jsonrpc": "2.0"
  },
  {
    "id": 2,
    "method": "add",
    "params": [
      11,
      "thirteen"
    ],
    "jsonrpc": "2.0"
  }
]
```

Example Result Out

```json
[
  {
    "id": 1,
    "result": 4,
    "jsonrpc": "2.0"
  },
  {
    "id": 2,
    "error": {
      "code": -32603,
      "message": "Internal error",
      "data": "Failed to deserialize request param [thirteen] to type [<class 'int'>]"
    },
    "jsonrpc": "2.0"
  }
]
```
