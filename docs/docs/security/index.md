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

We will use Pydantic to define data models, passlib to hash and salt passwords,
python-jose to encode/decode user data in JWTs, and Sanic for networking.

Overview:

## OpenRPC Security Extension

First we'll cover the OpenRPC security extension provided by this framework.

## Depends Arguments

We pass extra `Depends` arguments to the framework to be accessed and used by RPC
methods.

## Authentication Overview

Next we create a user and store user data. Then, a sign-in process, will verify
user credentials and return a [JWT](https://jwt.io/) with encoded user data.

## Authorization Overview

Then we will write a server that pulls JWTs from request headers, decodes the token,
and passes security data to the framework to check permissions.
