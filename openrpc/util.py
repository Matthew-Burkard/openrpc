import json
import logging
from json import JSONDecodeError
from typing import Union, Callable, Type

from open_rpc_objects import ContentDescriptorObject, SchemaObject
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
            error_resp = ErrorResponseObject.from_dict(resp)
            if resp['error'].get('data'):
                error_resp.error = ErrorObjectData(**resp['error'])
            else:
                error_resp.error = ErrorObject(**resp['error'])
            return error_resp
        if 'result' in resp.keys():
            return ResultResponseObject.from_dict(resp)
        raise JSONRPCError('Unable to parse response.')
    except (JSONDecodeError, TypeError, AttributeError) as e:
        log.exception(f'{type(e).__name__}:')
        raise JSONRPCError('Unable to parse response.')


def get_openrpc_params(fun: Callable) -> list[ContentDescriptorObject]:
    # noinspection PyUnresolvedReferences
    return [
        ContentDescriptorObject(name, get_schema(annotation))
        for name, annotation in fun.__annotations__.items()
    ]


def get_openrpc_result(fun: Callable) -> ContentDescriptorObject:
    print(fun)  # TODO
    return ContentDescriptorObject('result', SchemaObject())


def get_schema(annotation: Type) -> SchemaObject:
    print(annotation)  # TODO
    return SchemaObject()


def get_schema_type_from_py_type(annotation: Type) -> str:
    py_to_schema = {
        'str': 'string',
        'int': 'number',
        'float': 'number',
        'bool': 'boolean',
    }
    return ''
