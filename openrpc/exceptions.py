from typing import Type, Optional, Union

from openrpc.rpc_objects import (
    INVALID_REQUEST, INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND,
    PARSE_ERROR, ErrorObjectData, ErrorObject,
)


class JSONRPCError(Exception):
    def __init__(self, *args) -> None:
        super(JSONRPCError, self).__init__(*args)


class ParseError(JSONRPCError):
    def __init__(self) -> None:
        super(ParseError, self).__init__(
            f'JSON RPC Error: {PARSE_ERROR[0]}: {PARSE_ERROR[1]}',
        )


class InvalidRequest(JSONRPCError):
    def __init__(self) -> None:
        super(InvalidRequest, self).__init__(
            f'JSON RPC Error: {INVALID_REQUEST[0]}: {INVALID_REQUEST[1]}',
        )


class MethodNotFound(JSONRPCError):
    def __init__(self) -> None:
        super(MethodNotFound, self).__init__(
            f'JSON RPC Error: {METHOD_NOT_FOUND[0]}: {METHOD_NOT_FOUND[1]}',
        )


class InvalidParams(JSONRPCError):
    def __init__(self) -> None:
        super(InvalidParams, self).__init__(
            f'JSON RPC Error: {INVALID_PARAMS[0]}: {INVALID_PARAMS[1]}',
        )


class InternalError(JSONRPCError):
    def __init__(self) -> None:
        super(InternalError, self).__init__(
            f'JSON RPC Error: {INTERNAL_ERROR[0]}: {INTERNAL_ERROR[1]}',
        )


class ServerError(JSONRPCError):
    def __init__(self, error: Union[ErrorObjectData, ErrorObject]) -> None:
        msg = f'{error.code}: {error.message}'
        if isinstance(error, ErrorObjectData):
            msg += f'\nError Data: {error.data}'
        super(ServerError, self).__init__(msg)


def get_exception(code: int) -> Optional[Type]:
    return {
        -32700: ParseError,
        -32600: InvalidRequest,
        -32601: MethodNotFound,
        -32602: InvalidParams,
        -32603: InternalError,
    }.get(code)
