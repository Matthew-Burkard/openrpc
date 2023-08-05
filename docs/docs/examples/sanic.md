---
id: Sanic
slug: /examples/sanic
sidebar_position: 2
---

# Sanic

[Sanic](https://sanic.dev/en/) server exposing an OpenRPC server over HTTP and
Websocket.

```python
from openrpc import RPCServer
from sanic import HTTPResponse, Request, Sanic, text, Websocket

app = Sanic("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


@app.websocket("/api/v1/")
async def ws_process_rpc(_request: Request, ws: Websocket) -> None:
    """Process RPC requests through websocket."""
    async for msg in ws:
        json_rpc_response = await rpc.process_request_async(msg)
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)


@app.post("/api/v1/")
async def http_process_rpc(request: Request) -> HTTPResponse:
    """Process RPC request through HTTP server."""
    json_rpc_response = await rpc.process_request_async(request.body)
    return text(json_rpc_response, headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```
