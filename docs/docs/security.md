---
slug: /security/scopes
sidebar_position: 6
---

# Security

## Permission Scopes

In order to define a permission scope use the `Scope` class.
To require a permission when calling a method include, the scope in the `method` annotation.

```python
add_numbers = Scope(name="numbers:add", description="Permission to add two numbers.")


@rpc.method(scopes=[add_numbers])
async def add(a: int, b: int) -> int:
    return a + b
```

Then, when calling the `RPCApp.process` method, pass it a context object that
includes the permission scopes of the given request.

If every required scope name is in the context scopes list, the method call will be
called, otherwise an `RPCPermissionError` will be raised.

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
        scopes=_get_scopes_from_token(request.headers["Authorization"])
    )
    return web.Response(body=await rpc.process(await request.text(), context))


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", api)
    web.run_app(app)
```

## Scope Groups (OR of ANDs)

The `scopes` argument requires the caller to hold **every** listed scope (logical
AND). To allow **any one** of several alternative permission sets, use the
`scope_groups` argument. Each group is an AND set, and access is granted if the
caller satisfies **all** scopes of **any** single group (logical OR across groups).

```python
admin = Scope(name="admin")
numbers_read = Scope(name="numbers:read")
service = Scope(name="service")


@rpc.method(
    scope_groups=[
        [admin, numbers_read],  # group 1: admin AND numbers:read
        [service],              # group 2: service
    ]
)
async def add(a: int, b: int) -> int:
    return a + b
```

The call above is permitted when the caller holds both `admin` and
`numbers:read`, **or** when it holds `service`. If neither group is fully
satisfied an `RPCPermissionError` is raised.

`scopes` and `scope_groups` can be combined; the legacy `scopes` list is treated
as an additional group. The grouped requirement is serialized in `rpc.discover`
under the `x-scope-groups` extension field, while `x-scopes` continues to expose
the legacy flat `scopes` list unchanged.
