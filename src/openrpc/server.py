import re
from functools import partial
from typing import (
    Callable,
    Type,
    Any,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

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

    def method(
            self,
            *args: Union[T, tuple[T]],
            method: Optional[MethodObject] = None
    ) -> T:
        if args:
            func = args[0]
            method = MethodObject()
            return self.server.method(func, method)
        return partial(self.server.method, method=method)

    def process_request(self, data: Union[bytes, str]) -> Optional[str]:
        return self.server.process(data)

    def discover(self) -> OpenRPCObject:
        for name, rpc_method in self.server.methods.items():
            if name == 'rpc.discover':
                continue
            method = rpc_method.method
            method.params = method.params or self._get_params(rpc_method.fun)
            method.result = method.result or self._get_result(rpc_method.fun)
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

    def _get_params(self, fun: Callable) -> list[ContentDescriptorObject]:
        return [
            ContentDescriptorObject(
                name=name,
                schema=self._get_schema(annotation),
                required=self._is_required(annotation)
            )
            for name, annotation in get_type_hints(fun).items()
            if name != 'return'
        ]

    def _get_result(self, fun: Callable) -> ContentDescriptorObject:
        return ContentDescriptorObject(
            name='result',
            schema=self._get_schema(get_type_hints(fun)['return']),
            required=self._is_required(get_type_hints(fun)['return'])
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
                schema.title = schema.title or name
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
                    for k, v in get_type_hints(annotation).items()
                    if k != 'return'
                }
            if schema not in self.components.schemas.values():
                self.components.schemas[name] = schema
            return SchemaObject(**{'$ref': f'#/components/schemas/{name}'})

        if schema_type == 'array':
            schema = SchemaObject()
            schema.type = schema_type
            if args := get_args(annotation):
                schema.items = SchemaObject(**self._get_properties(args[0]))
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
            return [
                self._py_to_schema_type(arg)
                if '__name__' in dir(arg) and arg.__name__ != 'NoneType'
                else 'null'
                for arg in args
            ]
        return py_to_schema.get(annotation) or 'object'

    def _get_properties(self, annotation: Type) -> dict[str, Any]:
        schema = self._get_schema(annotation)
        properties = {}
        if isinstance(schema, list):
            types = [arg.ref if arg.ref else arg.type for arg in schema]
            types = list(dict.fromkeys(types))
            if len(types) > 1:
                # noinspection PyTypedDict
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
