<div align=center>
  <h1>OpenRPC</h1>
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg"
   height="20"
   alt="License: AGPL v3">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg"
   height="20"
   alt="Code style: black">
  <img src="https://img.shields.io/pypi/v/openrpc.svg"
   height="20"
   alt="PyPI version">
  <a href="https://gitlab.com/mburkard/openrpc/-/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/static/v1.svg?label=Contributions&message=Welcome&color=2267a0"
     height="20"
     alt="Contributions Welcome">
  </a>
  <h3>OpenRPC provides classes to rapidly develop an
  <a href="https://open-rpc.org">OpenRPC</a> server.</h3>
</div>

## Installation

OpenRPC is on PyPI and can be installed with:

```shell
pip install openrpc
```

## Usage

This library provides an `RPCServer` class that can be used to quickly
create an OpenRPC Server; it needs at minimum a title and version.

```python
from openrpc.server import RPCServer

rpc = RPCServer(title="Demo Server", version="1.0.0")
```

### Register a function as an RPC Method

To register a method with the RPCServer add the `@rpc.method` decorator
to a function.

```python
@rpc.method
def add(a: int, b: int) -> int:
    return a + b
```

### Process JSON RPC Request

OpenRPC is transport agnostic. To use it, pass JSON RPC requests to the
`process_request` method.

```python
req = """
{
  "id": 1,
  "method": "add",
  "params": {"a": 2, "b": 2},
  "jsonrpc": "2.0"
}
"""
rpc.process_request(req)  # '{"id": 1, "result": 4, "jsonrpc": "2.0}'
```

### RPC Discover

The `rpc.discover` method is automatically generated. It relies heavily
on type hints.

### Pydantic Support

For data classes to work properly use Pydantic.
RPCServer will use Pydantic for JSON serialization/deserialization as
well as generating schemas when calling `rpc.discover`.

### Async Support (v1.2+)

RPCServer has async support:

```python
await rpc.process_request_async(req)
```

## Example

```python
from flask import Flask, request

from openrpc.server import RPCServer

app = Flask(__name__)
rpc = RPCServer(title="Demo Server", version="1.0.0")


@rpc.method
def add(a: int, b: int) -> int:
    return a + b


@app.route("/api/v1/", methods=["POST"])
def process_rpc() -> str:
    return rpc.process_request(request.data)


if __name__ == "__main__":
    app.run()
```

Example In

```json
[
  {
    "id": 1,
    "method": "add",
    "params": {"a": 1, "b": 3},
    "jsonrpc": "2.0"
  }, {
    "id": 2,
    "method": "add",
    "params": [11, "thirteen"],
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
  }, {
    "id": 2,
    "error": {
      "code": -32000,
      "message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
    },
    "jsonrpc": "2.0"
  }
]
```
