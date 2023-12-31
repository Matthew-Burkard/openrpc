---
id: Python OpenRPC
slug: /
sidebar_position: 1
---

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

While Python OpenRPC is a transport agnostic framework, if you're going to expose your
RPC API over websockets or HTTP it is recommended you
use [Tabella](https://gitlab.com/mburkard/tabella) which wraps this framework.

```shell
pip install tabella
```

Or with [Poetry](https://python-poetry.org/)

```shell
poetry add tabella
```

Or to use the framework directly.

```shell
pip install openrpc
```

```shell
poetry add openrpc
```

## Example

This is a minimal OpenRPC server hosted over HTTP and WebSockets
using [Tabella](https://gitlab.com/mburkard/tabella).

```python
from tabella import Tabella

rpc = Tabella(title="DemoServer", version="1.0.0")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    rpc.run()
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
