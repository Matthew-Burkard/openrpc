![](https://img.shields.io/badge/License-MIT-blue.svg)
![](https://img.shields.io/badge/code%20style-black-000000.svg)
![](https://img.shields.io/pypi/v/openrpc.svg)
![](https://img.shields.io/badge/coverage-100%25-success)

**Documentation**: https://python-openrpc.burkard.cloud

**Source Code**: https://gitlab.com/mburkard/openrpc

Python OpenRPC is a transport agnostic framework for quickly and easily
developing [OpenRPC](https://open-rpc.org/) servers in Python.

## Requirements

- Python 3.14+
- [Pydantic](https://docs.pydantic.dev/latest/) for data models.

## Installation

```shell
uv add openrpc
```

Or

```shell
pip install openrpc
```

## Example

This is a minimal OpenRPC server hosted over HTTP using [aiohttp](https://docs.aiohttp.org/en/stable/).

```python
from aiohttp import web
from openrpc import RPCApp

rpc = RPCApp()


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


async def api(request: web.Request) -> web.Response:
    return web.Response(body=await rpc.process(await request.text()))


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", api)
    web.run_app(app)
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

## Support the Developer

<a href="https://www.buymeacoffee.com/mburkard" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me a Coffee"
       width="217"
       height="60"/>
</a>
