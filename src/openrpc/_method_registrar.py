"""Module providing method registrar interface."""

from __future__ import annotations

__all__ = ("MethodRegistrar", "CallableType")

import inspect
import logging
import typing
from typing import Annotated, Any, Callable, Union, get_args, get_origin

from py_undefined import Undefined
from pydantic import create_model

from openrpc._common import MethodMetaData, RPCMethod, resolved_annotation
from openrpc._depends import DependsModel, InjectModel
from openrpc._objects import (
    CallableType,
    ContentDescriptor,
    Error,
    ExamplePairing,
    ExternalDocumentation,
    Link,
    ParamStructure,
    Server,
    Tag,
)
from openrpc._request_processor import RequestProcessor
from openrpc._context import BaseContext

log = logging.getLogger("openrpc")


class MethodRegistrar:
    """Interface for registering RPC methods."""

    def __init__(self) -> None:
        """Initialize a new instance of the MethodRegistrar class."""
        self._rpc_methods: dict[str, RPCMethod] = {}
        self._method_by_function: dict[Callable[..., Any], RPCMethod] = {}
        self._request_processor = RequestProcessor(debug=False)
        self._warn = True

    @property
    def debug(self) -> bool:
        """Debug logging status."""
        return self._request_processor.debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._request_processor.debug = debug

    def method(  # noqa: PLR0913
        self,
        name: str | None = None,
        params: list[ContentDescriptor] | None = None,
        result: ContentDescriptor | None = None,
        tags: list[Tag | str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        external_docs: ExternalDocumentation | None = None,
        deprecated: bool | None = None,  # noqa: FBT001
        servers: list[Server] | None = None,
        errors: list[Error] | None = None,
        links: list[Link] | None = None,
        param_structure: ParamStructure | None = None,
        examples: list[ExamplePairing] | None = None,
        security: dict[str, list[str]] | None = None,
        scopes: list[str] | None = None,
    ) -> Callable[[CallableType], CallableType]:
        """Register a method with this OpenRPC server.

        :param name: The canonical name for the method.
        :param params: A list of parameters that are applicable for this method.
        :param result: The description of the result returned by the method.
        :param tags: A list of tags for API documentation control.
        :param summary: A short summary of what the method does.
        :param description: A verbose explanation of the method behavior.
        :param external_docs: Additional external documentation for this method.
        :param deprecated: Declares this method to be deprecated.
        :param servers: An alternative servers array to service this method.
        :param errors: A list of custom application defined errors that MAY be returned.
        :param links: A list of possible links from this method call.
        :param param_structure: The expected format of the parameters
        :param examples: Array of Example Pairing Objects.
        :param security: Scheme and scopes required to call this method.
        :param scopes: Permissions required to call this method.
        :return: The method decorator.
        """
        tag_objects = (
            [tag if isinstance(tag, Tag) else Tag(name=tag) for tag in tags]
            if tags is not None
            else None
        )

        def _decorator(function: CallableType) -> CallableType:
            return self._method(
                function,
                MethodMetaData(
                    name=name or function.__name__,
                    params=params,
                    result=result,
                    tags=tag_objects,
                    summary=summary,
                    description=description,
                    external_docs=external_docs,
                    deprecated=deprecated,
                    servers=servers,
                    errors=errors,
                    links=links,
                    param_structure=param_structure,
                    examples=examples,
                    security=security or {},
                    scopes=scopes or [],
                ),
            )

        return _decorator

    def remove(self, method: str) -> None:
        """Remove a method from this server by name.

        :param method: Name of the method to remove.
        :return: None.
        """
        rpc_method = self._rpc_methods.pop(method)
        _ = self._method_by_function.pop(rpc_method.function)
        _ = self._request_processor.methods.pop(method)

    def _method(  # noqa: PLR0912, PLR0915
        self, function: CallableType, metadata: MethodMetaData
    ) -> CallableType:
        signature = inspect.signature(function)

        # Get field information from each method parameter.
        depends: dict[str, DependsModel] = {}
        inject: list[InjectModel] = []
        fields: dict[str, Any] = {}
        schema_fields: dict[str, Any] = {}
        required: list[str] = []
        context_arg: tuple[str, int] | None = None
        type_hints = typing.get_type_hints(function)
        for key in signature.parameters:
            if key not in type_hints:
                type_hints[key] = Any
        for i, param_name in enumerate([t for t in type_hints if t != "return"]):
            param = signature.parameters[param_name]
            default: Any | Undefined = param.default
            annotation: Any = param.annotation
            if isinstance(param.default, DependsModel):
                depends[param_name] = param.default
                continue
            if get_origin(annotation) is Annotated and isinstance(
                (inject_fun := get_args(annotation)[1]), DependsModel
            ):
                depends[param_name] = inject_fun
                continue
            if get_origin(annotation) is Annotated and isinstance(
                (inject_fun := get_args(annotation)[1]), InjectModel
            ):
                inject_param = inject_fun
                inject_param.index = i
                inject_param.name = param_name
                inject.append(inject_param)
                continue
            # If multiple args have a type subclassing context, only use the first.
            try:
                if (
                    issubclass(type_hints[param_name], BaseContext)
                    and context_arg is None
                ):
                    context_arg = param_name, i
                    continue
            except TypeError:
                pass  # Needed for python 3.14+
            if Undefined in (args := typing.get_args(annotation)):
                default = Undefined
                # Remove `Undefined` from annotation for Pydantic.
                new_args = tuple(arg for arg in args if arg is not Undefined)
                origin = typing.get_origin(annotation)
                if hasattr(origin, "__name__") and origin.__name__ == "UnionType":
                    # This line is not covered in python 3.9 but later versions need it.
                    annotation = Union[new_args]  # type: ignore
                else:
                    annotation = origin[new_args]
            elif param.default is Undefined:
                default = Undefined
            elif param.default is inspect.Signature.empty:
                required.append(param_name)
                # Pyright has an issue with this only when running in Python 3.9
                default = ...  # pyright: ignore[reportUnknownVariableType]
            fields[param_name] = (
                resolved_annotation(annotation, function),
                default,
            )
            schema_fields[param_name] = (
                resolved_annotation(annotation, function),
                default if default is not Undefined else ...,
            )

        # Params model.
        param_model = create_model(f"{metadata.name}.params", **fields)
        # Params model.
        param_schema_model = create_model(f"{metadata.name}.params", **schema_fields)

        # Result Model
        result_model = create_model(
            f"{metadata.name}.result",
            # Pyright has an issue with this only when running in Python 3.9
            result=(
                resolved_annotation(signature.return_annotation, function),
                ...,
            ),  # pyright: ignore[reportUnknownArgumentType]
        )

        # Add method to processor method list.
        rpc_method = RPCMethod(
            context_arg=context_arg,
            depends=depends,
            inject=inject,
            function=function,
            metadata=metadata,
            params_model=param_model,
            params_schema_model=param_schema_model,
            required=required,
            result_model=result_model,
        )
        self._rpc_methods[metadata.name] = rpc_method
        self._method_by_function[function] = rpc_method
        log.debug(
            "Registering function [%s] as method [%s]", function.__name__, metadata.name
        )
        self._request_processor.method(rpc_method, metadata.name)
        return function
