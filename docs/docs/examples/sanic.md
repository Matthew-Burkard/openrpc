---
id: Sanic
slug: /examples/sanic
sidebar_position: 2
---

# Sanic

The following is an example of a [Sanic](https://sanic.dev/en/) server exposing an
OpenRPC server over HTTP and Websocket.

```python
import json

import sanic
from openrpc import RPCServer
from sanic import Request, Sanic, Websocket
from sanic.response import JSONResponse

app = Sanic("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


@app.websocket("/api/v1/")
async def process_websocket(_request: Request, ws: Websocket) -> None:
    async for msg in ws:
        json_rpc_response = await rpc.process_request_async(msg)
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)


@app.post("/api/v1/", name="HTTP API")
async def process_websocket(request: Request) -> JSONResponse:
    json_rpc_response = await rpc.process_request_async(request.body)
    return sanic.json(json.loads(json_rpc_response))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```
