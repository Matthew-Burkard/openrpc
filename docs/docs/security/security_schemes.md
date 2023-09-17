---
slug: /security/schemes
sidebar_position: 3
---

# OpenRPC Security Extension

The OpenRPC spec
allows [extensions](https://spec.open-rpc.org/#specification-extensions). This framework
adds a security scheme extension.
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

```python
rpc = RPCServer(security_schemes={"apikey": APIKeyAuth()})


@rpc.method(security={"apikey": []})
def require_apikey() -> bool:
    return True
```

## Passing Security Data to RPC Method Calls

When a security scheme is set for a method, any call to that method will raise a
permission error unless the same security scheme and scopes are provided
to the `rpc.process_request` call, e.g.

```python
request = '{"id": 1, "method": "require_apikey", "jsonrpc": "2.0"}'
rpc.process_request(request, security={"apikey": []))
```
