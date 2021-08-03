import json
import logging
from json import JSONDecodeError
from typing import Union

from openrpc.exceptions import JSONRPCError
from rpc_objects import (
    ResponseType, ErrorResponseObject, ResultResponseObject, ErrorObjectData,
    ErrorObject,
)

__all__ = ('parse_response',)
log = logging.getLogger(__name__)


def parse_response(data: Union[bytes, str]) -> ResponseType:
    try:
        resp = json.loads(data)
        if resp.get('error'):
            error_resp = ErrorResponseObject(**resp)
            if resp['error'].get('data'):
                error_resp.error = ErrorObjectData(**resp['error'])
            else:
                error_resp.error = ErrorObject(**resp['error'])
            return error_resp
        if 'result' in resp.keys():
            return ResultResponseObject(**resp)
        raise JSONRPCError('Unable to parse response.')
    except (JSONDecodeError, TypeError, AttributeError) as e:
        log.exception(f'{type(e).__name__}:')
        raise JSONRPCError('Unable to parse response.')
