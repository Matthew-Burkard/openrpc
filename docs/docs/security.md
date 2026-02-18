---
slug: /security/scopes
sidebar_position: 6
---

# Security

## Permission Scopes

In order to define a permission scope use the `Scope` class.
To require a permission in a method include the scope in the `method` annotation.

Then, when calling the `RPCApp.process` method, pass it a context object that
includes the permission scopes of the given request.

If every required scope name is in the context scopes method call will continue,
otherwise an `RPCPermissionError` will be raised.


```python
from aiohttp import web
from openrpc import BaseContext, RPCApp, Scope

rpc = RPCApp()

add_numbers = Scope(name="numbers:add", description="Permission to add two numbers.")


@rpc.method(scopes=[add_numbers])
async def add(a: int, b: int) -> int:
    return a + b


def _get_scopes_from_token(token: str) -> list[str]: ...


async def api(request: web.Request) -> web.Response:
    context = BaseContext(
        scopes=_get_scopes_from_auth(request.headers["Authorization"])
    )
    return web.Response(body=await rpc.process(await request.text(), context))


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", api)
    web.run_app(app)
```

