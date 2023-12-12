---
slug: /security/schemes
sidebar_position: 1
---

# Security Schemes

## OpenRPC Security Extension

The OpenRPC spec
allows [extensions](https://spec.open-rpc.org/#specification-extensions). This framework
adds a security scheme extension to enable the built-in security handling detailed
below.
The [Components Object](https://spec.open-rpc.org/#components-object) has an added field
`x_security_schemes` (
[aliased](https://docs.pydantic.dev/latest/usage/fields/#field-aliases)
to `x-securitySchemes`). This field is used to identify and describe the security
schemes used by an API and is largely the same as in
[OAS 3](https://swagger.io/docs/specification/authentication/). Security schemes can be
provided to the `RPCServer` instantiation.

The [Method Object](https://spec.open-rpc.org/#method-object) has an added
field `x_security` (
[aliased](https://docs.pydantic.dev/latest/usage/fields/#field-aliases)
to `x-security`). The security data on a method is a dictionary of the scheme name to a
list of scopes.

If a method caller lacks the proper security scheme a permission error will be raised
with a code of `-32099`.

## Using Python-OpenRPC Security Schemes

### Set Security Scheme and Scopes for a Method

When decorating a function as an RPC method you can specify required security schemes
and scopes as such:

```python
@rpc.method(security={"apikey": []})
def require_apikey() -> bool:
    """Method caller needs a valid API Key."""
    return True

@rpc.method(security={"apikey": ["scope1", "scope2"]})
def require_apikey_with_permissions() -> bool:
    """Caller needs API Key with permissions `scope1` and `scope2`."""
    return True
```

### Setting the Security Function

In order for the framework to know the scheme and scopes of a method caller
the RPCServer `security_function` needs to be set.

When a security scheme is set for a method, any call to that method will raise a
permission error unless the same security scheme and scopes are returned from the
configured security function.

The security function will be called with each method call and will be passed
the `caller_details` that are provided to the `process_request`
or `process_request_async` method call.

### Example Using FastAPI and Request Headers

This example passes request headers sent to an HTTP endpoint to
the `process_request_async` call, then the `security_function` is made to get
the `Authorization` header and use that to determine the caller security scheme and
scopes.

```python
import uvicorn
from fastapi import FastAPI, Response
from openrpc import APIKeyAuth, RPCServer
from starlette.datastructures import Headers
from starlette.requests import Request


app = FastAPI()

security_scheme = {"apikey": APIKeyAuth()}
rpc = RPCServer(security_schemes=security_scheme)


def security_function(caller_details: Headers) -> dict[str, list[str]]:
    """Determine security scheme of method caller from request headers."""
    access_token = caller_details["Authorization"]
    # Real app will decode token and find user/permissions.
    token_permissions = {"token1": [], "token2": ["scope1", "scope2"]}
    return {"apikey": token_permissions[access_token]}


@rpc.method(security={"apikey": []})
def require_apikey() -> bool:
    """Method caller needs a valid API Key."""
    return True


@rpc.method(security={"apikey": ["scope1", "scope2"]})
def require_apikey_with_permissions() -> bool:
    """Caller needs API Key with permissions `scope1` and `scope2`."""
    return True


@app.post("/api/v1")
async def http_process_rpc(request: Request) -> Response:
    """Process RPC request through HTTP server."""
    rpc_response = await rpc.process_request_async(
        await request.body(), caller_details=request.headers
    )
    return Response(content=rpc_response, media_type="application/json")


if __name__ == "__main__":
    rpc.security_function = security_function
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

#### Using the Example

```shell
# Requests with `token1` can call `require_apikey` but not `require_apikey_with_permissions`.
curl 'http://localhost:8080/api/v1' -H 'Authorization: token1' --data-raw '{"id": 1, "method": "require_apikey", "jsonrpc": "2.0"}'
{"id":1,"result":true,"jsonrpc":"2.0"}

curl 'http://localhost:8080/api/v1' -H 'Authorization: token1' --data-raw '{"id": 1, "method": "require_apikey_with_permissions", "jsonrpc": "2.0"}'
{"id":1,"error":{"code":-32099,"message":"Permission error"},"jsonrpc":"2.0"}

# Requests with `token2` can call both `require_apikey` and `require_apikey_with_permissions`.
curl 'http://localhost:8080/api/v1' -H 'Authorization: token2' --data-raw '{"id": 1, "method": "require_apikey", "jsonrpc": "2.0"}'
{"id":1,"result":true,"jsonrpc":"2.0"}

curl 'http://localhost:8080/api/v1' -H 'Authorization: token2' --data-raw '{"id": 1, "method": "require_apikey_with_permissions", "jsonrpc": "2.0"}'
{"id":1,"result":true,"jsonrpc":"2.0"}
```

# Depends Arguments

Your methods may need to use caller details to determine the specific user
calling a method, not just the security scheme. You can inject values to a method call
by writing `Depends` functions to access `caller_details` and return those values.

We're going to write a function to get the calling user from `caller_details` called
`get_user`. Then we use the function by making the default value of a
method argument equal to `Depends(get_user)`.

## Example Combining `Depends` and Security Function

```python
import uvicorn
from fastapi import FastAPI, Response
from openrpc import APIKeyAuth, Depends, RPCServer
from starlette.datastructures import Headers
from starlette.requests import Request

app = FastAPI()

security_scheme = {"apikey": APIKeyAuth()}
rpc = RPCServer(security_schemes=security_scheme)
db = {
    "token1": {
        "username": "user1",
        "security_schemes": {"apikey": ["scope1"]},
    }
}


def get_user(caller_details: Headers) -> dict[str, list[str]]:
    """Get user calling a method."""
    access_token = caller_details["Authorization"]
    # Real app will get user from decoding token.
    user = db[access_token]
    return user


def security_function(user: dict = Depends(get_user)) -> dict[str, list[str]]:
    """Determine security scheme of method caller from request headers."""
    return user["security_schemes"]


@rpc.method(security={"apikey": ["scope1"]})
def require_apikey_with_permission() -> bool:
    """Caller needs API Key with permission `scope1`."""
    return True


@rpc.method(security={"apikey": ["scope1"]})
def get_caller(user: dict = Depends(get_user)) -> dict:
    """Get the calling user."""
    return user


@app.post("/api/v1")
async def http_process_rpc(request: Request) -> Response:
    """Process RPC request through HTTP server."""
    rpc_response = await rpc.process_request_async(
        await request.body(), caller_details=request.headers
    )
    return Response(content=rpc_response, media_type="application/json")


if __name__ == "__main__":
    rpc.security_function = security_function
    uvicorn.run(app, host="0.0.0.0", port=8080)
```
