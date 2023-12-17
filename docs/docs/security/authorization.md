---
slug: /security/authorization
sidebar_position: 3
---

# Authorization

With authentication and the frameworks built-in security handling covered we can put it
all together with a complete example of a sign-up and sign-in process. Using
authentication and the Python OpenRPC security schemes and `Depends` values.

```python
import datetime

import bcrypt
import uvicorn
from fastapi import FastAPI, Response
from jose import jwt
from openrpc import BearerAuth, Depends, RPCServer
from pydantic import BaseModel
from starlette.datastructures import Headers
from starlette.requests import Request

# openssl rand -hex 32
SECRET_KEY = "f5d94a66702b1c932df8e4e4aa99402ab581d2e19883c618b67d5593af05c9c7"
ALGORITHM = "HS256"

db = {}
app = FastAPI()
security_scheme = {"Bearer": BearerAuth()}
rpc = RPCServer(security_schemes=security_scheme, debug=True)


class User(BaseModel):
    username: str
    hashed_password: str
    security_schemes: dict[str, list[str]]


class Token(BaseModel):
    access_token: str
    token_type: str


def get_user(caller_details: Headers) -> User:
    """Get caller user object from request headers."""
    auth = caller_details.get("Authorization")
    if auth is None:
        raise PermissionError("No user is signed in.")
    access_token = auth.removeprefix("Bearer ")
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    user = db[payload["username"]]
    return user


def security_function(
    _caller_details: Headers, user: User = Depends(get_user)
) -> dict[str, list[str]]:
    """Determine security scheme of method caller using `Depends`."""
    return user.security_schemes


def _create_access_token(data: dict, lifespan: datetime.timedelta) -> str:
    """Create an access token with encoded data."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + lifespan
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@rpc.method()
def sign_up(username: str, password: str) -> None:
    """Create a new user."""
    byte_password = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(byte_password, bcrypt.gensalt()).decode()
    user = User(
        username=username,
        hashed_password=hashed_password,
        security_schemes={"Bearer": []},
    )
    db[user.username] = user


@rpc.method()
def sign_in(username: str, password: str) -> Token:
    """Get a JWT for an existing user."""
    user = db[username]
    # Incorrect password.
    if not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        raise Exception("Authentication failed.")

    return Token(
        access_token=_create_access_token(
            data={"username": user.username}, lifespan=datetime.timedelta(hours=1.0)
        ),
        token_type="bearer",
    )


@rpc.method(security={"Bearer": []})
def get_caller(user: User = Depends(get_user)) -> User:
    """Get the user calling this method."""
    return user


@rpc.method(security={"Bearer": ["scope1"]})
def require_scopes() -> bool:
    """Require caller to have security scope `scope`."""
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
