---
slug: /security/depends_arguments
sidebar_position: 2
---

# Depends Arguments

Your methods may need to use request headers or connection details to determine the user
calling a method.

It's possible to supply additional values from the framework to a function when an RPC
method is called. We're going to supply a method with user data to determine if a user
can call that method.

Dependent arguments must be supplied to the process_request or process_request_async
methods in a dictionary. The dictionary will be a map of dependent argument name to
value with the name as a string.

In order to access a dependent argument from a function add a parameter to the function
with a name matching the key from the dictionary and a default value of `Depends` from
openrpc.

```python
from openrpc import Depends, RPCServer

rpc = RPCServer(title="RPCServer", version="1.0.0", debug=True)


@rpc.method()
def add(a: int, b: int, user: dict = Depends) -> int:
    if "add" not in user["permissions"]:
        raise PermissionError('The "add" permission is required to call this method.')
    return a + b


user = {"email": "email@test.com", "permissions": ["add"]}
request = '{"id": 1, "method": "add", "params": [1, 3], "jsonrpc": "2.0"}'
json_rpc_response = rpc.process_request(request, depends={"user": user})
```

Before Python OpenRPC calls a function it checks for any arguments in that function with
a default value of Depends. If it finds any such arguments, it uses the argument name to
find the value with that key name in the `depends` dictionary passed to process_request.

It's important to note that any `Depends` arguments are not exposed to the OpenRPC API,
the add method above still only expects two integer parameters.
