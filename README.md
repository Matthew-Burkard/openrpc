<div align=center>
  <h1>OpenRPC</h1>
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg"
   height="20"
   alt="License: AGPL v3">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg"
   height="20"
   alt="Code style: black">
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

## Example Usage

```python
from flask import Flask, Response, jsonify, request
from openrpc.server import OpenRPCServer

app = Flask(__name__)
rpc = OpenRPCServer(title='Demo Server', version='1.0.0')


@rpc.method
def add(x: float, y: float) -> float:
    return x + y


@app.route('/api/v1/', methods=['POST'])
def process_rpc() -> Response:
    return jsonify(rpc.process_request(request.json))


if __name__ == '__main__':
    app.run()
```

Example In

```json
{
  "method": "add",
  "params": [
    1,
    2
  ],
  "id": 1,
  "jsonrpc": "2.0"
}
```

Example Result Out

```json
{
  "id": 1,
  "result": 3,
  "jsonrpc": "2.0"
}
```

Example Error Out

```json
{
  "id": 1,
  "error": {
    "code": -32000,
    "message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
  },
  "jsonrpc": "2.0"
}
```

## RPC Discover

The `rpc.discover` method for the server is automatically generated using
Python type hints. Output for the example server above would be:

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
          "name": "x",
          "schema": {
            "type": "number"
          },
          "required": true
        },
        {
          "name": "y",
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
