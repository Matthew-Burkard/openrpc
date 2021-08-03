from typing import Callable, Type, Any, Optional, Union, get_args

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
            uncaught_error_code: Optional[int] = None
    ) -> None:
        self.server = RPCServer(title, version, uncaught_error_code)
        self.schemas: list[SchemaObject] = []
        self.server.method(
            method=MethodObject(name='rpc.discover')
        )(self.discover)

    def method(
            self,
            *args,
            method: Optional[Union[Callable, MethodObject]] = None
    ) -> Callable:
        return self.server.method(*args, method=method)

    def process(self, data: Union[bytes, str]) -> Optional[str]:
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
            openrpc='1.2.6',
            info=InfoObject(
                title=self.server.title,
                version=self.server.version
            ),
            methods=[it.method for it in self.server.methods.values()
                     if it.method.name != 'rpc.discover']
        ).json(by_alias=True, exclude_unset=True)

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

    def _get_schema(
            self,
            annotation: Type,
            name: Optional[str] = None
    ) -> SchemaObject:
        # TODO Create definitions and references.
        schema = SchemaObject()
        schema_type = self._get_schema_type_from_py_type(annotation)
        if schema_type == 'object':
            # pydantic
            if 'schema' in dir(annotation):
                # noinspection PyUnresolvedReferences
                schema = SchemaObject(**annotation.schema())
                if schema not in self.schemas:
                    self.schemas.append(schema)
                return schema

            # noinspection PyUnresolvedReferences
            schema.properties = [
                self._get_schema(v, k)
                for k, v in annotation.__init__.__annotations__.items()
                if k != 'return'
            ]
        schema.title = name or annotation.__name__
        schema.type = schema_type
        return schema

    @staticmethod
    def _get_schema_type_from_py_type(annotation: Any) -> str:
        if args := get_args(annotation):
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
        return 'NoneType' in [a.__name__ for a in get_args(annotation)]
