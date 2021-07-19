import json
from dataclasses import dataclass
from typing import Optional, Union

from jsonrpc2.json_types import JSON, JSONArray, JSONObject

PARSE_ERROR = (-32700, 'Parse error')
INVALID_REQUEST = (-32600, 'Invalid Request')
METHOD_NOT_FOUND = (-32601, 'Method not found')
INVALID_PARAMS = (-32602, 'Invalid params')
INTERNAL_ERROR = (-32603, 'Internal error')


# TODO Separate these into different objects for Notifications and
#  requests and responses that re missing optional members.
@dataclass
class RPCRequest:
    method: str
    params: Optional[Union[JSONArray, JSONObject]] = None
    id: Optional[Union[str, int]] = None
    jsonrpc: str = '2.0'

    def to_json(self) -> str:
        ret_val = {'method': self.method, 'jsonrpc': self.jsonrpc}
        if self.id is not None:
            ret_val['id'] = self.id
        if self.params is not None:
            ret_val['params'] = self.params
        return json.dumps(ret_val)


@dataclass
class RPCError:
    code: int
    message: str
    data: JSON = None

    def to_json(self) -> str:
        ret_val = {'code': self.code, 'message': self.message}
        if self.data is not None:
            ret_val['data'] = self.data
        return json.dumps(ret_val)


@dataclass
class RPCResponse:
    id: Optional[Union[str, int]] = None
    result: JSON = None
    error: Optional[RPCError] = None
    jsonrpc: str = '2.0'

    def to_json(self) -> str:
        ret_val = {'jsonrpc': self.jsonrpc}
        if self.id is not None:
            ret_val['id'] = self.id
        # This MUST be kept if/else. None is a valid value for result.
        if self.error is not None:
            ret_val['error'] = json.loads(self.error.to_json())
        else:
            ret_val['result'] = self.result
        return json.dumps(ret_val)

    @staticmethod
    def from_json(data: Union[bytes, str]) -> 'RPCResponse':
        data = json.loads(data)
        if error := data.get('error'):
            data['error'] = RPCError(**error)
        return RPCResponse(**data)
