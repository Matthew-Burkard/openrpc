---
slug: /security/depends_arguments
sidebar_position: 2
---

# Depends Arguments

Your methods may need to use request headers or connection details to determine the user
calling a method. It's possible to supply additional values from the framework to a
function when an RPC method is called using `Depends` arguments.

The headers need to be passed to `process_request` or `process_request_async` as
`middleware_args` to be accessed from a method. The method calls in this example will
use a hard-coded dictionary in place of request headers to remain transport agnostic.

In order to use the `middleware_args` write a function that accepts the middleware args
as an argument and returns the value you want passed to an RPC method. The one in this
example is `get_user`. Then you can use the function by making the default value of a
method argument equal to `Depends(get_user)`.

## Example of `Depends` in use.

```python
import json
from typing import Any

from openrpc import Depends, RPCServer

rpc = RPCServer(title="DependsExample", version="1.0.0")


def get_user(middleware_args: dict) -> dict[str, Any]:
    """Function that uses middleware args."""
    token = middleware_args["Authorization"].removeprefix("Bearer ")
    # In production this would be replaced with logic to decode the
    # token and get the user from a database.
    return {
        "eyJhbGciJIUzI1NiIsICI6IkpXVCJ9": {"id": "14ac680e-ecec-42a7-8cad-c1d2ec58b491"}
    }[token]


@rpc.method()
def get_user_id(user: dict[str, Any] = Depends(get_user)) -> str:
    """RPC method that gets a value from a `Depends` function."""
    return user["id"]


if __name__ == "__main__":
    headers = {"Authorization": "Bearer eyJhbGciJIUzI1NiIsICI6IkpXVCJ9"}
    request = '{"id": 1, "method": "get_user_id", "jsonrpc": "2.0"}'
    resp = json.loads(rpc.process_request(request, headers))
    assert resp["result"] == "14ac680e-ecec-42a7-8cad-c1d2ec58b491"
```
