---
slug: /security/authorization
sidebar_position: 4
---

# Authorization

## Requirements

- [passlib](https://pypi.org/project/passlib/)
- [python-jose](https://pypi.org/project/python-jose/)
- [Sanic](https://pypi.org/project/sanic/)
- [Pydantic](https://pypi.org/project/pydantic/)

## Authorization Tutorial

Now that users are authenticated, we want to authorize method access.

Create an `RPCServer` with a security scheme and add our `sign_in` and `sign_up`
functions from the `authentication` guide as OpenRPC methods.

```python
from openrpc import BearerAuth, RPCServer

rpc = RPCServer(security_schemes={"bearer": BearerAuth()}, debug=True)


@rpc.method()
def sign_up(username: str, password: str) -> User:
    ...


@rpc.method()
def sign_in(username: str, password: str) -> Token:
    ...
```

Now we create a method with security requirements and a `Depends` argument.

```python
@rpc.method(security={"bearer": []})
def require_token(user: User = Depends) -> User:
    return user
```

### Getting User Data from JWTs

Using Sanic, we're going pull access tokens from request headers, decode them, and use
the decoded information to find the user that made the request and pass that information
to `process_request_async` calls so the framework can supply that data to our functions.

We'll use the following function to get `depends` arguments and `security` from request
headers to be passed to `rpc.process_request_async`.

```python
def get_depends_and_security(
    headers: dict[str, str]
) -> tuple[User | None, dict | None]:
    # Get bearer token from headers.
    auth = headers.get("Authorization")
    if auth is None:
        return None, None
    # If token is present use it to get user data.
    auth = auth.removeprefix("Bearer ")
    payload = jwt.decode(auth, SECRET_KEY, algorithms=[ALGORITHM])
    return {"user": db[payload["username"]]}, {"bearer": []}
```

Now we call this function passing it request headers from WbSocket connection or HTTP
request.

```python
import asyncio

from sanic import HTTPResponse, Request, Sanic, text, Websocket


@app.websocket("/api/v1/")
async def ws_process_rpc(request: Request, ws: Websocket) -> None:
    """Process RPC requests through websocket."""
    depends, security = get_depends_and_security(request.headers.get("Authorization"))

    async def _process_rpc(rpc_req: str) -> None:
        response = await rpc.process_request_async(rpc_req, depends, security)
        if response is not None:
            await ws.send(response)

    async for msg in ws:
        asyncio.create_task(_process_rpc(msg))
    await ws.close()


@app.post("/api/v1/")
async def http_process_rpc(request: Request) -> HTTPResponse:
    """Process RPC request through HTTP server."""
    depends, security = get_depends_and_security(request.headers.get("Authorization"))
    response = await rpc.process_request_async(request.body, depends, security)
    return text(response, headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Complete Example

Putting this all together we have a complete app that can create users, authenticate a
user, and authorize use of a method based on user permissions.

```python
import asyncio
from datetime import datetime, timedelta

from jose import jwt
from openrpc import BearerAuth, Depends, RPCServer
from passlib.context import CryptContext
from pydantic import BaseModel
from sanic import HTTPResponse, Request, Sanic, text, Websocket

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["scrypt"])
db = {}

app = Sanic("RPCServer")
rpc = RPCServer(security_schemes={"bearer": BearerAuth()}, debug=True)


class User(BaseModel):
    username: str
    hashed_password: str


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


@rpc.method(security={"bearer": []})
def require_token(user: User = Depends) -> User:
    return user


def get_depends_and_security(
    headers: dict[str, str]
) -> tuple[dict[str, User] | None, dict[str : list[str]] | None]:
    # Get bearer token from headers.
    auth = headers.get("Authorization")
    if auth is None:
        return None, None
    # If token is present use it to get user data.
    auth = auth.removeprefix("Bearer ")
    payload = jwt.decode(auth, SECRET_KEY, algorithms=[ALGORITHM])
    return {"user": db[payload["username"]]}, {"bearer": []}


@app.websocket("/api/v1/")
async def ws_process_rpc(request: Request, ws: Websocket) -> None:
    """Process RPC requests through websocket."""
    depends, security = get_depends_and_security(request.headers)

    async def _process_rpc(rpc_req: str) -> None:
        response = await rpc.process_request_async(rpc_req, depends, security)
        if response is not None:
            await ws.send(response)

    async for msg in ws:
        asyncio.create_task(_process_rpc(msg))
    await ws.close()


@app.post("/api/v1/")
async def http_process_rpc(request: Request) -> HTTPResponse:
    """Process RPC request through HTTP server."""
    depends, security = get_depends_and_security(request.headers)
    response = await rpc.process_request_async(request.body, depends, security)
    return text(response, headers={"Content-Type": "application/json"})


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
    call("sign_up", ["email@test.com", "password"])
    token = call("sign_in", ["email@test.com", "password"])["access_token"]
    token_header = {"Authorization": f"Bearer {token}"}
    assert call("require_token", [], token_header)["username"] == "email@test.com"
```
