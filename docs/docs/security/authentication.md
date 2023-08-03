---
slug: /security/authentication
sidebar_position: 1
---

# Authentication

We are going to write two functions to handle user authentication:

- `sign_up` create a user, hash and salt the password, store user data.
- `sign_in` verify a username and password, return an access token.

## Requirements

- [passlib](https://pypi.org/project/passlib/)
- [python-jose](https://pypi.org/project/python-jose/)
- [Pydantic](https://pypi.org/project/pydantic/)

## Authentication Tutorial

### User

Before we can write these functions we need to create a user object and means to store
it. We are going to use a Pydantic model to represent users and store the data in a
dictionary called `db`.

We are also going to create a model to store the access token used by `sign_in`.

```python
from pydantic import BaseModel

db = {}


class User(BaseModel):
    username: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
```

### Sign Up

Next we can add the `sign_up` method to create and store a user. Using `CryptContext`
from passlib we hash and salt the password before we store user data.

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["scrypt"])


def sign_up(username: str, password: str) -> None:
    """Create a new user."""
    user = User(username=username, hashed_password=pwd_context.hash(password))
    db[user.username] = user
```

### Sign In

`sign_in` will take a username and password, find the user based on username and verify
the provided password against the stored one using the `pwd_context` we created earlier.

If sign in is successful we create a JWT using python-jose and return it in a `Token`
object. The token is encoded using a key that can be generated with
`openssl rand -hex 32`. We will use `HS256` algorithm.

```python
from jose import jwt

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"


def sign_in(username: str, password: str) -> Token:
    """Get a JWT for an existing user."""
    user = db[username]
    if not pwd_context.verify(password, user.hashed_password):
        raise Exception("Authentication failed.")
    return Token(
        access_token=_create_access_token(data={"username": user.username}),
        token_type="bearer",
    )


def _create_access_token(data: dict) -> str:
    """Create an access token with encoded data."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1.0)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Complete Example

That covers the basics of user authentication, for reference below is a complete
example. Next we cover using this with permissions to authorize OpenRPC method calls.

```python
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["scrypt"])
db = {}


class User(BaseModel):
    username: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str


def sign_up(username: str, password: str) -> User:
    """Create a new user."""
    user = User(username=username, hashed_password=pwd_context.hash(password))
    db[user.username] = user
    return user


def sign_in(username: str, password: str) -> Token:
    """Get a JWT for an existing user."""
    user = db[username]
    if not pwd_context.verify(password, user.hashed_password):
        raise Exception("Authentication failed.")
    return Token(
        access_token=_create_access_token(data={"username": user.username}),
        token_type="bearer",
    )


def _create_access_token(data: dict) -> str:
    """Create an access token with encoded data."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1.0)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```
