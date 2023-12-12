---
slug: /security/authentication
sidebar_position: 2
---

# Authentication

## Requirements

- [bcrypt](https://pypi.org/project/bcrypt/)
- [python-jose](https://pypi.org/project/python-jose/)
- [Pydantic](https://pypi.org/project/pydantic/)

## Authentication Tutorial

We are going to write two functions to handle user authentication:

- `sign_up` create a user, hash and salt the password, store user data.
- `sign_in` verify a username and password, return an access token.

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

Next we can add the `sign_up` method to create and store a user. Using `bcrypt`
we hash and salt the password before we store user data.

```python
import bcrypt


def sign_up(username: str, password: str) -> None:
    """Create a new user."""
    byte_password = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(byte_password, bcrypt.gensalt()).decode()
    user = User(username=username, hashed_password=hashed_password)
    db[user.username] = user
```

### Sign In

`sign_in` will take a username and password, find the user based on username and verify
the provided password against the stored one using `bcrypt.checkpw`.

If sign in is successful we create a JWT using `python-jose` and return it in a `Token`
object. The token is encoded using a key that can be generated with
`openssl rand -hex 32`. We will use `HS256` algorithm.

```python
import datetime

import bcrypt
from jose import jwt
from pydantic import BaseModel

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"

...


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


def _create_access_token(data: dict, lifespan: datetime.timedelta) -> str:
    """Create an access token with encoded data."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + lifespan
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Complete Example

That covers the basics of user authentication, for reference below is a complete
example. Next we cover using this with permissions to authorize OpenRPC method calls.

```python
import datetime

import bcrypt
from jose import jwt
from pydantic import BaseModel

# openssl rand -hex 32
SECRET_KEY = "9e852f19194dfb55e33c81ad21e44ec21d3819755970abf9c2c2852cb6bca19e"
ALGORITHM = "HS256"

db = {}


class User(BaseModel):
    username: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def sign_up(username: str, password: str) -> None:
    """Create a new user."""
    byte_password = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(byte_password, bcrypt.gensalt()).decode()
    user = User(username=username, hashed_password=hashed_password)
    db[user.username] = user


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


def _create_access_token(data: dict, lifespan: datetime.timedelta) -> str:
    """Create an access token with encoded data."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + lifespan
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```
