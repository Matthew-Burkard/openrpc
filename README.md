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

This library provides an `OpenRPCServer` class that can be used to
quickly create an OpenRPCServer; it takes as an argument an `InfoObject`
which needs at minimum a title and version.

```python
from openrpc.objects import InfoObject
from openrpc.server import OpenRPCServer

rpc = OpenRPCServer(InfoObject(title="Demo Server", version="1.0.0"))
```

### Register a function as an RPC Method

To register a method with the OpenRPCServer add the `@rpc.method`
decorator to a method.

```python
@rpc.method
def add(a: int, b: int) -> int:
    return a + b
```

#### RPC Discover

The `rpc.discover` method is automatically generated. It relies heavily
on type hints.

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

## Async Support (v1.2+)

OpenRPC has async support:

```python
rpc.process_request_async(req)
```

## Example

```python
from flask import Flask, Response, request
from openrpc.objects import InfoObject
from openrpc.server import OpenRPCServer

app = Flask(__name__)
rpc = OpenRPCServer(InfoObject(title="Demo Server", version="1.0.0"))


@rpc.method
def add(a: int, b: int) -> int:
    return a + b


@app.route("/api/v1/", methods=["POST"])
def process_rpc() -> Response:
    return rpc.process_request(request.json)


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
    "params": [5, 7],
    "jsonrpc": "2.0"
  }, {
    "id": 3,
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
    "result": 12,
    "jsonrpc": "2.0"
  }, {
    "id": 3,
    "error": {
      "code": -32000,
      "message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
    },
    "jsonrpc": "2.0"
  }
]
```

Example RPC Discover

```json
{
  "openrpc": "1.2.6",
  "info": {
    "title": "Demo Server",
    "version": "1.0.0"
  },
  "methods": [
    {
      "name": "add",
      "params": [
        {
          "name": "a",
          "schema": {
            "type": "number"
          },
          "required": true
        },
        {
          "name": "b",
          "schema": {
            "type": "number"
          },
          "required": true
        }
      ],
      "result": {
        "name": "result",
        "schema": {
          "type": "number"
        },
        "required": true
      }
    }
  ],
  "components": {
    "schemas": {}
  }
}
```
