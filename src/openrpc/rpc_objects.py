from typing import Union, Optional, Any

from pydantic import BaseModel

PARSE_ERROR = (-32700, 'Parse error')
INVALID_REQUEST = (-32600, 'Invalid Request')
METHOD_NOT_FOUND = (-32601, 'Method not found')
INVALID_PARAMS = (-32602, 'Invalid params')
INTERNAL_ERROR = (-32603, 'Internal error')

RequestType = Union[
    'RequestObjectParams',
    'RequestObject',
    'NotificationObject',
    'NotificationObjectParams',
]
ResponseType = Union[
    'ErrorResponseObject',
    'ResultResponseObject',
]


class RequestObjectParams(BaseModel):
    id: Union[str, int]
    method: str
    params: Union[list, dict]
    jsonrpc: str = '2.0'


class RequestObject(BaseModel):
    id: Union[str, int]
    method: str
    jsonrpc: str = '2.0'


class NotificationObject(BaseModel):
    method: str
    jsonrpc: str = '2.0'


class NotificationObjectParams(BaseModel):
    method: str
    params: Union[list, dict]
    jsonrpc: str = '2.0'


class ErrorObjectData(BaseModel):
    code: int
    message: str
    data: Any


class ErrorObject(BaseModel):
    code: int
    message: str


class ErrorResponseObject(BaseModel):
    id: Optional[Union[str, int]]
    error: Union[ErrorObjectData, ErrorObject]
    jsonrpc: str = '2.0'


class ResultResponseObject(BaseModel):
    id: Union[str, int]
    result: Any
    jsonrpc: str = '2.0'
