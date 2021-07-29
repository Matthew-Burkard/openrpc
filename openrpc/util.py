import json
import logging
import typing
from json import JSONDecodeError
from typing import Union, Callable, Type, Any

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
        ContentDescriptorObject(
            name,
            get_schema(name, annotation),
            required=is_required(annotation)
        )
        for name, annotation in fun.__annotations__.items()
    ]


def get_openrpc_result(fun: Callable) -> ContentDescriptorObject:
    print(fun)  # TODO
    return ContentDescriptorObject('result', SchemaObject())


def get_schema(name: str, annotation: Type) -> SchemaObject:
    print(annotation)
    # TODO Move all of this openrpc logic to class for generating
    #  openrpc JSON. It should create a schema for every object it
    #  encounters and store it off and use a reference. If it encounters
    #  an object that it already encountered before, use the existing
    #  reference.
    return SchemaObject()


def get_schema_type_from_py_type(annotation: Any) -> str:
    if args := typing.get_args(annotation):
        # FIXME Kinda hacky.
        annotation = args[0]
    py_to_schema = {
        None: 'null',
        str: 'string',
        int: 'number',
        float: 'number',
        bool: 'boolean',
    }
    return py_to_schema.get(annotation) or 'object'


def is_required(annotation: Any) -> bool:
    return 'NoneType' in [a.__name__ for a in typing.get_args(annotation)]
