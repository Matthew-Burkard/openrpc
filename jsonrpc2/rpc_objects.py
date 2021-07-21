from dataclasses import dataclass
from typing import Union

from dataclasses_json import dataclass_json

from jsonrpc2.json_types import JSON, JSONStructured

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


@dataclass_json
@dataclass
class RequestObjectParams:
    id: Union[str, int]
    method: str
    params: JSONStructured
    jsonrpc: str = '2.0'


@dataclass_json
@dataclass
class RequestObject:
    id: Union[str, int]
    method: str
    jsonrpc: str = '2.0'


@dataclass_json
@dataclass
class NotificationObject:
    method: str
    jsonrpc: str = '2.0'


@dataclass_json
@dataclass
class NotificationObjectParams:
    method: str
    params: JSONStructured
    jsonrpc: str = '2.0'


@dataclass_json
@dataclass
class ErrorObjectData:
    code: int
    message: str
    data: JSON = None


@dataclass_json
@dataclass
class ErrorObject:
    code: int
    message: str


@dataclass_json
@dataclass
class ErrorResponseObject:
    id: Union[str, int]
    error: Union[ErrorObject, ErrorObjectData]
    jsonrpc: str = '2.0'


@dataclass_json
@dataclass
class ResultResponseObject:
    id: Union[str, int]
    result: JSON = None
    jsonrpc: str = '2.0'
