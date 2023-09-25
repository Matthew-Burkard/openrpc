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

This is a minimal OpenRPC server hosted over HTTP and WebSockets
using [Tabella](https://gitlab.com/mburkard/tabella)
and [uvicorn](https://www.uvicorn.org/).

```python
from openrpc import RPCServer
import tabella

rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


app = tabella.get_app(rpc)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
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

A [template app](https://gitlab.com/mburkard/openrpc-app-template) is available as an
example or to clone to bootstrap your RPC server.

## Support the Developer

<a href="https://www.buymeacoffee.com/mburkard" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me a Coffee"
       width="217"
       height="60"/>
</a>
