# Python OpenRPC

![](https://img.shields.io/badge/License-MIT-blue.svg)
![](https://img.shields.io/badge/code%20style-black-000000.svg)
![](https://img.shields.io/pypi/v/openrpc.svg)
![](https://img.shields.io/badge/coverage-100%25-success)

**Documentation**: https://python-openrpc.burkard.cloud

**Source Code**: https://gitlab.com/mburkard/openrpc

Python OpenRPC is a transport agnostic framework for quickly and easily
developing [OpenRPC](https://open-rpc.org/) servers in Python.

## Requirements

- Python 3.9+
- [Pydantic](https://docs.pydantic.dev/latest/) for data models.

## Installation

OpenRPC is on PyPI and can be installed with:

```shell
pip install openrpc
```

Or with [Poetry](https://python-poetry.org/)

```shell
poetry add openrpc
```

## Example

This is a minimal OpenRPC server using a [Sanic](https://sanic.dev/en/) websocket server
as the transport method.

```python
import asyncio

from openrpc import RPCServer
from sanic import Request, Sanic, Websocket

app = Sanic("DemoServer")
rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


@app.websocket("/api/v1/")
async def ws_process_rpc(_request: Request, ws: Websocket) -> None:
    async def _process_rpc(request: str) -> None:
        json_rpc_response = await rpc.process_request_async(request)
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)

    async for msg in ws:
        asyncio.create_task(_process_rpc(msg))


if __name__ == "__main__":
    app.run()
```

Example In

```json
{
  "id": 1,
  "method": "add",
  "params": {
    "a": 1,
    "b": 3
  },
  "jsonrpc": "2.0"
}
```

Example Result Out

```json
{
  "id": 1,
  "result": 4,
  "jsonrpc": "2.0"
}
```

## Template App

You can bootstrap your OpenRPC server by cloning the
[template app](https://gitlab.com/mburkard/openrpc-app-template).

## Support the Developer

<a href="https://www.buymeacoffee.com/mburkard" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me a Coffee"
       width="217"
       height="60"/>
</a>
