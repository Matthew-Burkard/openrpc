---
title: Security
sidebar_position: 4
---

# User Authentication and Authorization

Your project will probably need user authentication and likely need permissions on a
by-method basis. Implementation of authentication will vary since Python OpenRPC is
transport agnostic, for this example we will be using JWT tokens over HTTP and
websockets.

This guide requires [passlib](https://pypi.org/project/passlib/),
[python-jose](https://pypi.org/project/python-jose/),
[Sanic](https://pypi.org/project/sanic/), and
[Pydantic](https://pypi.org/project/pydantic/)

### Pre-Made App Template

A pre-made Python OpenRPC template app doing all of this can be found
[here](https://gitlab.com/mburkard/openrpc-app-template).

## Authentication Overview

We're going to create a user, store user info in a [JWT](https://jwt.io/), store that
token in a request header, decode the token. This will use passlib to hash and salt
passwords, and python-jose to encode user info in a JWT.

## Authorization Overview

Once we have an authenticated user we will create a system of permissions for users
with authorization to determine whether a user may call a given method. We will pull
the JWT from request headers and use it to get the user for to check permissions.
