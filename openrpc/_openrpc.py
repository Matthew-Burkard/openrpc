import typing
from typing import Callable, Type, Any

from open_rpc_objects import ContentDescriptorObject, SchemaObject


def get_params(fun: Callable) -> list[ContentDescriptorObject]:
    # noinspection PyUnresolvedReferences
    return [
        ContentDescriptorObject(
            name,
            _get_schema(name, annotation),
            required=_is_required(annotation)
        )
        for name, annotation in fun.__annotations__.items()
    ]


def get_result(fun: Callable) -> ContentDescriptorObject:
    print(fun)  # TODO
    return ContentDescriptorObject('result', SchemaObject())


def _get_schema(name: str, annotation: Type) -> SchemaObject:
    print(annotation)
    return SchemaObject()


def _get_schema_type_from_py_type(annotation: Any) -> str:
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


def _is_required(annotation: Any) -> bool:
    return 'NoneType' in [a.__name__ for a in typing.get_args(annotation)]
