---
id: Sanic
slug: /examples/sanic
sidebar_position: 2
---

# Sanic as Transport

[Sanic](https://sanic.dev/en/)

## Websocket

```python
from openrpc import RPCServer
from sanic import Request, Sanic, Websocket

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


if __name__ == "__main__":
    app.run()
```
