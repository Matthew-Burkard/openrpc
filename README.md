# Usage Examples

## Example Flask Server
```python
from flask import Flask, Response, jsonify, request
from rpc_server import RPCServer

app = Flask(__name__)
rpc = RPCServer()


@rpc.register
def add(x: float, y: float) -> float:
    return x + y

@app.route('/api/v1/operations/', methods=['POST'])
def operations() -> Response:
    return jsonify(rpc.process(request.json))


if __name__ == '__main__':
    app.run()
```
Example In
```json
{
  "method": "add",
  "params": [1, 2],
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
    "message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
    "data": null
  },
  "jsonrpc": "2.0"
}
```
