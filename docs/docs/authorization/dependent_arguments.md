---
slug: /dependent-arguments
sidebar_position: 1
---

# Authorization

Your project will probably need user authentication and perhaps even permissions on a
by-method basis. Implementation of authorization will vary since Python OpenRPC is
transport agnostic, for this example we will be using JWT tokens with HTTP and
websockets.

We're going to create a user, store user info in a [JWT](https://jwt.io/), store that
token in a request header, decode the token, and pass user information to a called
method.

## Dependent Arguments

It's possible to supply additional values from the framework to a function when an RPC
method is called. We're going to supply a method with user data to determine if a user
can call that
method.

Additional arguments must be supplied to the `process_request` or
`process_request_async` methods in a dictionary. In order to access a dependent argument
to a function add a parameter to the function with a name matching the key from the
dictionary and a default value of `Depends` from `openrpc`.

#### Example Dependency Passed to a Function

```python
from openrpc import Depends, RPCServer

rpc = RPCServer(title="DemoServer", version="1.0.0")


@rpc.method()
def add(a: int, b: int, user: dict = Depends) -> int:
    if "add" not in user["permissions"]:
        raise PermissionError()
    return a + b


user = {"email": "email@test.com", "permissions": ["add"]}
request = '{"id": 1, "method": "add", "params": [1, 3], "jsonrpc": "2.0"}'
json_rpc_response = rpc.process_request(request, {"user": user})
```
