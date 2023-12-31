---
slug: /undefined_values
sidebar_position: 4
---

# Undefined Values

If you need to write a method that only uses a parameter if that parameter is present in
the request to the method. You can write something like this:

```python
from openrpc import RPCServer

rpc = RPCServer()

@rpc.method()
async def update(a: str | None = None, b: str | None = None) -> None
    if a is not None:
        ...  # Update a.
    if b is not None:
        ...  # Update b.
```

Given a request with the params: `{"b": "coffee"}`, only param `b` is provided so
only `b` will be updated. But there's a problem, what if `None` is a valid value? Given
the request params: `{"b": null}`, `b` won't be updated to `null`, nothing will happen.

In order to distinguish between a value of `null` and the parameter not being provided
at all, the default value of that parameter can be set to `Undefined`.

```python
from openrpc import RPCServer, Undefined

rpc = RPCServer()

@rpc.method()
async def update_values(a: str | None = Undefined, b: str | None = Undefined) -> None
    if a is not Undefined:
        ...  # Update a.
    if b is not Undefined:
        ...  # Update b.
```

With this method a request with params `{"b": null}` will leave `a` unaffected and
update `b` with a value of `None`.
