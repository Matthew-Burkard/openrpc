---
id: FastAPI
slug: /examples/fastapi
sidebar_position: 3
---

# FastAPI

[FastAPI](https://fastapi.tiangolo.com/) server exposing an OpenRPC server over HTTP and
Websocket.

```python
import asyncio
from typing import Union

import uvicorn
from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from jsonrpcobjects.objects import (
    ErrorResponse,
    Notification,
    ParamsNotification,
    ParamsRequest,
    Request,
    ResultResponse,
)
from openrpc import RPCServer

app = FastAPI()
RequestType = Union[ParamsRequest, Request, ParamsNotification, Notification]
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


@app.websocket("/api/v1")
async def ws_process_rpc(websocket: WebSocket) -> None:
    """Process RPC requests through websocket."""
    await websocket.accept()
    try:

        async def _process_rpc(request: str) -> None:
            json_rpc_response = await rpc.process_request_async(request)
            if json_rpc_response is not None:
                await websocket.send_text(json_rpc_response)

        while True:
            data = await websocket.receive_text()
            asyncio.create_task(_process_rpc(data))
    except WebSocketDisconnect:
        await websocket.close()


@app.post("/api/v1", response_model=Union[ErrorResponse, ResultResponse, None])
async def http_process_rpc(request: RequestType) -> Response:
    """Process RPC request through HTTP server."""
    json_rpc_response = await rpc.process_request_async(request.model_dump_json())
    return Response(content=json_rpc_response, media_type="application/json")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```
