---
id: Flask
slug: /examples/flask
sidebar_position: 2
---

# Flask

[Flask](https://flask.palletsprojects.com/en/2.3.x/) server exposing an OpenRPC server
over HTTP.

```python
from flask import Flask, request, Response
from openrpc import RPCServer

app = Flask("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
def add(a: int, b: int) -> int:
    return a + b


@app.route("/api/v1", methods=["POST"])
def http_process_rpc() -> tuple[Response, int]:
    """Process RPC request through HTTP server."""
    json_rpc_response = rpc.process_request(request.data)
    response = Response(json_rpc_response, content_type="application/json")
    return response, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```
