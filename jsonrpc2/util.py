import json
import logging
from json import JSONDecodeError
from typing import Union

from jsonrpc2.exceptions import JSONRPCError
from rpc_objects import ResponseType, ErrorResponseObject, ResultResponseObject

__all__ = ('parse_response',)
log = logging.getLogger(__name__)


def parse_response(data: Union[bytes, str]) -> ResponseType:
    try:
        resp = json.loads(data)
        if resp.get('error'):
            return ErrorResponseObject.from_dict(resp)
        if 'result' in resp.keys():
            return ResultResponseObject.from_dict(resp)
        raise JSONRPCError('Unable to parse response.')
    except (JSONDecodeError, TypeError, AttributeError) as e:
        log.exception(f'{type(e).__name__}:')
        raise JSONRPCError('Unable to parse response.')
