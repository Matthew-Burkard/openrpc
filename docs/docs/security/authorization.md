---
slug: /security/authorization
sidebar_position: 2
---

# Authorization

## Requirements

- [passlib](https://pypi.org/project/passlib/)
- [python-jose](https://pypi.org/project/python-jose/)
- [Sanic](https://pypi.org/project/sanic/)
- [Pydantic](https://pypi.org/project/pydantic/)

## Authorization Tutorial

Now that users are authenticated, we want to authorize method access based on user
permissions.

### Dependent Arguments

It's possible to supply additional values from the framework to a function when an RPC
method is called. We're going to supply a method with user data to determine if a user
can call that method.

Dependent arguments must be supplied to the `process_request` or `process_request_async`
methods in a dictionary. The dictionary will be a map of dependent argument name to
value with the name as a string.

In order to access a dependent argument from a function add a parameter to the function
with a name matching the key from the dictionary and a default value of `Depends`
from `openrpc`.

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
a default value of `Depends`. If it finds any such arguments, it uses the argument name
to find the value with that key name in the `depends` dictionary passed to
`process_request`.

It's important to note that any `Depends` arguments are not exposed to the OpenRPC API,
the `add` method above still only expects two integer parameters.

### Adding Methods with Permissions

Now that we can use a `Depends` argument to supply user information to a function, lets
tie that together with what we learned in the previous section to create a basic app
with authentication and authorization.

Going back to the example on authentication, lets add a new field to our `User` object
to store user permissions. We will have it default to a single permission of "add".

```python
class User(BaseModel):
    username: str
    hashed_password: str
    permissions: list[str] = Field(default_factory=lambda: ["add"])
```

Next we'll create an `RPCServer` and add our `sign_in` and `sign_up` functions as
OpenRPC methods.

```python
from openrpc import Depends, RPCServer

rpc = RPCServer(title="RPCServer", version="1.0.0", debug=True)


@rpc.method()
def sign_up(username: str, password: str) -> User:
    ...


@rpc.method()
def sign_in(username: str, password: str) -> Token:
    ...
```

Now we create two new methods using our `User` object to check if that user has
permission to call the method.

```python
@rpc.method()
def add(a: int, b: int, user: User = Depends) -> int:
    if "add" not in user.permissions:
        raise PermissionError('Permission "add" is required to call this method.')
    return a + b


@rpc.method()
def divide(a: int, b: int, user: User = Depends) -> float:
    if "divide" not in user.permissions:
        raise PermissionError('Permission "divide" is required to call this method.')
    return a / b
```

### Getting User Data from JWTs

Using Sanic, we're going pull access tokens from request headers, decode them, and use
the decoded information to find the user that made the request and pass that information
to `process_request_async` calls so the framework can supply that data to our functions.

First is the function to get user data from the `Authorization` header of a request:

```python
def _get_user(auth: str | None) -> User | None:
    if auth is None:
        return None
    token = auth.split()[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return db[payload["username"]]
```

Then we use that to get user data from request `Authorization` headers.

```python
from sanic import HTTPResponse, Request, Sanic, text, Websocket


@app.websocket("/api/v1/")
async def ws_process_rpc(request: Request, ws: Websocket) -> None:
    """Process RPC requests through websocket."""
    user = _get_user(request.headers.get("Authorization"))
    async for msg in ws:
        json_rpc_response = await rpc.process_request_async(msg, {"user": user})
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)
    await ws.close()


@app.post("/api/v1/")
async def http_process_rpc(request: Request) -> HTTPResponse:
    """Process RPC request through HTTP server."""
    user = _get_user(request.headers.get("Authorization"))
    json_rpc_response = await rpc.process_request_async(request.body, {"user": user})
    return text(json_rpc_response, headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Complete Example

Putting this all together we have a complete app that can create users, authenticate a
user, and authorize use of a method based on user permissions.

```python
from datetime import datetime, timedelta

from jose import jwt
from openrpc import Depends, RPCServer
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sanic import HTTPResponse, Request, Sanic, text, Websocket

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["scrypt"])
db = {}

app = Sanic("RPCServer")
rpc = RPCServer(title="RPCServer", version="1.0.0", debug=True)


class User(BaseModel):
    username: str
    hashed_password: str
    permissions: list[str] = Field(default_factory=lambda: ["add"])


class Token(BaseModel):
    access_token: str
    token_type: str


@rpc.method()
def sign_up(username: str, password: str) -> User:
    """Create a new user."""
    user = User(username=username, hashed_password=pwd_context.hash(password))
    db[user.username] = user
    return user


@rpc.method()
def sign_in(username: str, password: str) -> Token:
    """Get a JWT for an existing user."""
    user = db[username]
    if not pwd_context.verify(password, user.hashed_password):
        raise Exception("Authentication failed.")
    to_encode = {"username": user.username}
    expire = datetime.utcnow() + timedelta(hours=1.0)
    to_encode["exp"] = expire
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=token, token_type="bearer")


@rpc.method()
def add(a: int, b: int, user: User = Depends) -> int:
    if "add" not in user.permissions:
        raise PermissionError('Permission "add" is required to call this method.')
    return a + b


@rpc.method()
def divide(a: int, b: int, user: User = Depends) -> float:
    if "divide" not in user.permissions:
        raise PermissionError('Permission "divide" is required to call this method.')
    return a / b


def get_user(auth: str | None) -> User | None:
    if auth is None:
        return None
    token = auth.split()[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return db[payload["username"]]


@app.websocket("/api/v1/")
async def ws_process_rpc(request: Request, ws: Websocket) -> None:
    """Process RPC requests through websocket."""
    user = get_user(request.headers.get("Authorization"))
    async for msg in ws:
        json_rpc_response = await rpc.process_request_async(msg, {"user": user})
        if json_rpc_response is not None:
            await ws.send(json_rpc_response)
    await ws.close()


@app.post("/api/v1/")
async def http_process_rpc(request: Request) -> HTTPResponse:
    """Process RPC request through HTTP server."""
    user = get_user(request.headers.get("Authorization"))
    json_rpc_response = await rpc.process_request_async(request.body, {"user": user})
    return text(json_rpc_response, headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

It's worth noting, since the user data accessed from request headers, to call methods
after sign in from a websocket you must either establish a new connection with the auth
header or add means for the app to associate a websocket connection id with a user when
`sign_in` is called.

### Testing the Example

Here is an example of this app being used with a simple client leveraging
[httpx](https://pypi.org/project/httpx/).

```python
from typing import Any

import httpx


def call(method: str, params: list[Any], headers: dict[str, Any] | None = None) -> Any:
    headers = headers or {}
    headers["Content_type"] = "application/json"
    request = {"id": 1, "method": method, "params": params, "jsonrpc": "2.0"}
    response = httpx.post(
        "http://localhost:8080/api/v1", json=request, headers=headers
    ).json()
    if result := response.get("result"):
        return result
    return response["error"]


if __name__ == "__main__":
    call("sign_up", ["email@tesst.com", "password"])
    token = call("sign_in", ["email@tesst.com", "password"])["access_token"]
    token_header = {"Authorization": f"Bearer {token}"}
    assert call("add", [11, 13], token_header) == 24
    error = 'PermissionError: Permission "divide" is required to call this method.'
    assert call("divide", [11, 13], token_header)["data"] == error
```

## Abstracting the Permission Check

If your authorization process is like the one in this example it can be made simpler
to require permissions for a given method using the custom `RPCRouter` used here in the
[Python OpenRPC App Template](https://gitlab.com/mburkard/openrpc-app-template/-/blob/main/openrpc_app_template/common.py?ref_type=heads).
Examples of this custom router in use can be seen
[here](https://gitlab.com/mburkard/openrpc-app-template/-/blob/main/openrpc_app_template/api/math.py?ref_type=heads).
