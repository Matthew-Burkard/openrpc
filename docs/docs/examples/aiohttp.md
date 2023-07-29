---
slug: /examples/aiohttp
sidebar_position: 1
---

# Aiohttp

The following is an example of an [aiohttp](https://github.com/aio-libs/aiohttp) server
exposing an OpenRPC server over HTTP and Websocket.

```python
from aiohttp import web, WSMessage
from openrpc import RPCServer

rpc = RPCServer(title="TransportDemo", version="1.0.0")


@rpc.method()
def add(a: int, b: int) -> int:
    return a + b


async def ws_process_rpc(request: web.BaseRequest) -> web.WebSocketResponse:
    """Process RPC requests through websocket."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        msg: WSMessage = msg  # type: ignore
        response = await rpc.process_request_async(msg.data)
        if response is not None:
            await ws.send_str(response)

    return ws


async def http_process_rpc(request: web.Request) -> web.Response:
    """Process RPC request through HTTP server."""
    request_body = await request.text()
    response = await rpc.process_request_async(request_body)
    if response is not None:
        return web.Response(text=response)
    return web.Response()


def main() -> None:
    """Main entry point."""
    app = web.Application()
    app.router.add_route("GET", "/api/v1", ws_process_rpc)
    app.router.add_route("POST", "/api/v1", http_process_rpc)
    web.run_app(app)


if __name__ == "__main__":
    main()
```
