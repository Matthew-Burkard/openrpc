---
slug: /errors
sidebar_position: 9
---

# Errors

Any error parsing a JSON-RPC request or any error that occurs executing a function will
be wrapped in a
[JSON-RPC Error Object](https://www.jsonrpc.org/specification#error_object).

By default, the error returned will be a generic server error. The following:

```python
from openrpc import RPCServer

rpc = RPCServer(title="RPCServer", version="0.1.0")


@rpc.method()
def divide(a: int, b: int) -> float:
    return a / b


req = '{"id": 1, "method": "divide", "params": {"a": 2, "b": 0}, "jsonrpc": "2.0"}'
print(rpc.process_request(req))
```

Produces this error response:

```json
{
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Server error"
  },
  "jsonrpc": "2.0"
}
```

## Custom Errors

You will likely want errors that preserve the error code and message.

For that, create and error class that extends `OpenRPCError`.


```python
from openrpc import OpenRPCError, RPCServer

rpc = RPCServer(title="RPCServer", version="0.1.0")


class CustomError(OpenRPCError):
    """Error that will preserve custom code, message, and data."""

    def __init__(self, a: int, b: int, *args: object) -> None:
        """Instantiate custom error."""
        self.message = "Custom RPC error."
        self.code = -32002
        self.data = {"a": a, "b": b}
        super().__init__(self.code, self.message, self.data, *args)


@rpc.method()
def divide(a: int, b: int) -> float:
    """Divide two numbers."""
    try:
        return a / b
    except ZeroDivisionError as e:
        raise CustomError(a, b) from e


req = '{"id": 1, "method": "divide", "params": {"a": 2, "b": 0}, "jsonrpc": "2.0"}'
print(rpc.process_request(req))
```

Now error details are preserved.


```json
{
    "id": 1,
    "error": {
        "code": -32002,
        "message": "Custom RPC error.",
        "data": {
            "a": 2,
            "b": 0
        }
    },
    "jsonrpc": "2.0"
}
```


## Debug

In order to include error details in the error response set `debug=True` for the
`RPCServer`.

```python
rpc = RPCServer(title="RPCServer", version="0.1.0", debug=True)
```

Now the error response will contain error details in the data.
```json
{
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Server error",
    "data": "ZeroDivisionError: division by zero\n  File \"/home/matthew/Projects/openrpc-app/app.py\", line 8, in divide\n    return a / b\nZeroDivisionError: division by zero\n"
  },
  "jsonrpc": "2.0"
}
```
