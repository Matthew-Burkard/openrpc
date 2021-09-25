# OpenRPC

OpenRPC provides classes to rapidly develop an
[open-rpc](https://open-rpc.org/) server.

## Example Flask Server

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
