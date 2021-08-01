import typing
from typing import Callable, Type, Any

from open_rpc_objects import (
    ContentDescriptorObject, SchemaObject,
    OpenRPCObject, InfoObject, MethodObject,
)
from rpc_server import RPCServer


class OpenRPCServer:
    def __init__(
            self,
            title: str,
            version: str,
            uncaught_error_code: typing.Optional[int] = None
    ) -> None:
        self.server = RPCServer(title, version, uncaught_error_code)
        self.schemas: dict[str, SchemaObject] = {}
        self.server.method(
            method=MethodObject(name='rpc.discover')
        )(self.discover)

    def method(
            self,
            *args,
            method: typing.Optional[
                typing.Union[Callable, MethodObject]
            ] = None
    ) -> Callable:
        return self.server.method(*args, method=method)

    def process(self, data: typing.Union[bytes, str]) -> typing.Optional[str]:
        return self.server.process(data)

    def discover(self) -> str:
        for name, registered_method in self.server.methods.items():
            method = registered_method.method
            method.params = method.params or self.get_params(
                registered_method.fun
            )
            method.result = method.result or self.get_result(
                registered_method.fun
            )
        return OpenRPCObject(
            info=InfoObject(
                title=self.server.title,
                version=self.server.version
            ),
            methods=[it.method for it in self.server.methods.values()
                     if it.method.name != 'rpc.discover']
        ).json()

    def get_params(self, fun: Callable) -> list[ContentDescriptorObject]:
        # noinspection PyUnresolvedReferences
        return [
            ContentDescriptorObject(
                name=name,
                schema=self._get_schema(annotation),
                required=self._is_required(annotation)
            )
            for name, annotation in fun.__annotations__.items()
        ]

    def get_result(self, fun: Callable) -> ContentDescriptorObject:
        # noinspection PyUnresolvedReferences
        return ContentDescriptorObject(
            name='result',
            schema=self._get_schema(fun.__annotations__['return'])
        )

    def _get_schema(self, annotation: Type) -> SchemaObject:
        schema = SchemaObject()
        schema_type = self._get_schema_type_from_py_type(annotation)
        title = None
        if schema_type == 'object':
            title = annotation.__name__
            # TODO For property in annotation add SchemaObjectProperty.
        # TODO If new schema add to self.schemas, else use existing one.
        schema.title = title
        schema.type = schema_type
        return schema

    @staticmethod
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

    @staticmethod
    def _is_required(annotation: Any) -> bool:
        return 'NoneType' in [a.__name__ for a in typing.get_args(annotation)]
