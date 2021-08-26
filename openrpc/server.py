import re
from functools import partial
from typing import Callable, Type, Any, Optional, Union, get_args, get_origin

from openrpc._rpc_server import RPCServer
from openrpc.open_rpc_objects import (
    ContentDescriptorObject,
    SchemaObject,
    OpenRPCObject,
    InfoObject,
    MethodObject,
    ComponentsObject,
)

__all__ = ('OpenRPCServer',)
T = Type[Callable]


class OpenRPCServer:
    def __init__(
            self,
            title: str,
            version: str,
            uncaught_error_code: Optional[int] = None
    ) -> None:
        self.server = RPCServer(uncaught_error_code)
        self.title: str = title
        self.version: str = version
        self.components: ComponentsObject = ComponentsObject(schemas={})
        self.server.method(
            self.discover,
            method=MethodObject(name='rpc.discover')
        )

    def method(self, *f: tuple[T], method: Optional[MethodObject] = None) -> T:
        if f:
            func = f[0]
            method = MethodObject()
            return self.server.method(func, method)
        return partial(self.server.method, method=method)

    def process(self, data: Union[bytes, str]) -> Optional[str]:
        return self.server.process(data)

    def discover(self) -> OpenRPCObject:
        for name, registered_method in self.server.methods.items():
            if name == 'rpc.discover':
                continue
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
                title=self.title,
                version=self.version
            ),
            methods=[it.method for it in self.server.methods.values()
                     if it.method.name != 'rpc.discover'],
            components=self.components
        )

    def get_params(self, fun: Callable) -> list[ContentDescriptorObject]:
        # noinspection PyUnresolvedReferences
        return [
            ContentDescriptorObject(
                name=name,
                schema=self._get_schema(annotation),
                required=self._is_required(annotation)
            )
            for name, annotation in fun.__annotations__.items()
            if name != 'return'
        ]

    def get_result(self, fun: Callable) -> ContentDescriptorObject:
        # noinspection PyUnresolvedReferences
        return ContentDescriptorObject(
            name='result',
            schema=self._get_schema(fun.__annotations__['return']),
            required=self._is_required(fun.__annotations__['return'])
        )

    # noinspection PyUnresolvedReferences
    def _get_schema(self, annotation: Type) -> \
            Union[SchemaObject, list[SchemaObject]]:
        if get_origin(annotation) == Union:
            return [self._get_schema(arg) for arg in get_args(annotation)]

        schema_type = self._py_to_schema_type(annotation)

        if schema_type == 'object':
            try:
                name = annotation.__name__
            except AttributeError:
                name = None
            if 'schema' in dir(annotation):
                schema = SchemaObject(**annotation.schema())
                for k, v in (schema.definitions or {}).items():
                    if k not in self.components.schemas:
                        self.components.schemas[k] = v
                # pydantic creates definitions, move them to components.
                for prop in schema.properties.values():
                    if prop.ref:
                        prop.ref = re.sub(
                            r'^#/definitions',
                            '#/components/schemas',
                            prop.ref
                        )
                del schema.definitions
            elif get_origin(annotation) == dict:
                schema = SchemaObject()
                schema.type = schema_type
                schema.additional_properties = True
                return schema
            else:
                schema = SchemaObject()
                schema.type = schema_type
                schema.properties = {
                    k: self._get_schema(v)
                    for k, v in annotation.__init__.__annotations__.items()
                    if k != 'return'
                }
            if schema not in self.components.schemas.values():
                self.components.schemas[name] = schema
            return SchemaObject(**{'$ref': f'#/components/schemas/{name}'})

        if schema_type == 'array':
            schema = SchemaObject()
            schema.type = schema_type
            schema.items = {}
            # FIXME items will be overridden each iteration.
            for arg in get_args(annotation):
                schema.items = self._get_properties(arg)
            return schema

        schema = SchemaObject()
        schema.type = schema_type
        return schema

    def _py_to_schema_type(self, annotation: Any) -> Union[str, list[str]]:
        py_to_schema = {
            None: 'null',
            str: 'string',
            int: 'number',
            float: 'number',
            bool: 'boolean',
        }
        origin = get_origin(annotation)
        flat_collections = [list, set, tuple]
        if origin in flat_collections or annotation in flat_collections:
            return 'array'
        if dict in [origin, annotation]:
            return 'object'
        if Union in [origin, annotation]:
            return self._py_to_schema_type(get_args(annotation)[0])
        if args := get_args(annotation):
            return [self._py_to_schema_type(arg)
                    if '__name__' in dir(arg) and arg.__name__ != 'NoneType'
                    else 'null' for arg in args]
        return py_to_schema.get(annotation) or 'object'

    def _get_properties(self, annotation: Type) -> dict:
        schema = self._get_schema(annotation)
        properties = {}
        if isinstance(schema, list):
            types = [arg.ref if arg.ref else arg.type for arg in schema]
            types = list(dict.fromkeys(types))
            if len(types) > 1:
                properties['type'] = types
                return properties
            schema = schema[0]
        if schema.ref:
            properties['$ref'] = schema.ref
        else:
            properties['type'] = schema.type
        return properties

    @staticmethod
    def _is_required(annotation: Any) -> bool:
        return 'NoneType' in [a.__name__ for a in get_args(annotation)
                              if '__name__' in dir(a)]
