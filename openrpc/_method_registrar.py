"""Module providing method registrar interface."""

__all__ = ("MethodRegistrar", "CallableType")

import inspect
import logging
import typing
from typing import Any, Callable, Optional, TypeVar, Union

from py_undefined import Undefined
from pydantic import create_model

from openrpc._common import (
    MethodMetaData,
    resolved_annotation,
    RPCMethod,
)
from openrpc._depends import DependsModel
from openrpc._objects import (
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

log = logging.getLogger("openrpc")

CallableType = TypeVar("CallableType", bound=Callable)


class MethodRegistrar:
    """Interface for registering RPC methods."""

    def __init__(self) -> None:
        """Initialize a new instance of the MethodRegistrar class."""
        self._rpc_methods: dict[str, RPCMethod] = {}
        self._request_processor = RequestProcessor(debug=False)
        self._warn = True

    @property
    def debug(self) -> bool:
        """Debug logging status."""
        return self._request_processor.debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._request_processor.debug = debug

    def method(
        self,
        name: Optional[str] = None,
        params: Optional[list[ContentDescriptor]] = None,
        result: Optional[ContentDescriptor] = None,
        tags: Optional[list[Union[Tag, str]]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        external_docs: Optional[ExternalDocumentation] = None,
        deprecated: Optional[bool] = None,
        servers: Optional[list[Server]] = None,
        errors: Optional[list[Error]] = None,
        links: Optional[list[Link]] = None,
        param_structure: Optional[ParamStructure] = None,
        examples: Optional[list[ExamplePairing]] = None,
        security: Optional[dict[str, list[str]]] = None,
    ) -> Callable[[CallableType], CallableType]:
        """Register a method with this OpenRPC server.

        :param name: The canonical name for the method.
        :param params: A list of parameters that are applicable for this
            method.
        :param result: The description of the result returned by the
            method.
        :param tags: A list of tags for API documentation control.
        :param summary: A short summary of what the method does.
        :param description: A verbose explanation of the method
            behavior.
        :param external_docs: Additional external documentation for this
            method.
        :param deprecated: Declares this method to be deprecated.
        :param servers: An alternative servers array to service this
            method.
        :param errors: A list of custom application defined errors that
            MAY be returned.
        :param links: A list of possible links from this method call.
        :param param_structure: The expected format of the parameters
        :param examples: Array of Example Pairing Objects.
        :param security: Scheme and scopes required to call this method.
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
                ),
            )

        return _decorator

    def remove(self, method: str) -> None:
        """Remove a method from this server by name.

        :param method: Name of the method to remove.
        :return: None.
        """
        self._rpc_methods.pop(method)
        self._request_processor.methods.pop(method)

    def _method(self, function: CallableType, metadata: MethodMetaData) -> CallableType:
        signature = inspect.signature(function)

        # Get field information from each method parameter.
        depends = {}
        fields = {}
        schema_fields = {}
        required = []
        for param_name, param in signature.parameters.items():
            default: Any = param.default
            annotation: Any = param.annotation
            if isinstance(param.default, DependsModel):
                depends[param_name] = param.default
                continue
            if param.default is Undefined:
                default = Undefined
            elif Undefined in (args := typing.get_args(annotation)):
                default = Undefined
                # Remove `Undefined` from annotation for Pydantic.
                new_args = tuple(arg for arg in args if arg is not Undefined)
                origin = typing.get_origin(annotation)
                if hasattr(origin, "__name__") and origin.__name__ == "UnionType":
                    annotation = Union[new_args]
                else:
                    annotation = origin[new_args]  # type: ignore
            elif param.default is inspect.Signature.empty:
                required.append(param_name)
                default = ...
            fields[param_name] = (
                resolved_annotation(annotation, function),
                default,
            )
            schema_fields[param_name] = (
                resolved_annotation(annotation, function),
                default if default is not Undefined else ...,
            )

        # Params model.
        param_model = create_model(f"{metadata.name}Params", **fields)  # type: ignore
        # Params model.
        param_schema_model = create_model(  # type: ignore
            f"{metadata.name}Params", **schema_fields
        )

        # Result Model
        result_model = create_model(
            f"{metadata.name}Result",
            result=(resolved_annotation(signature.return_annotation, function), ...),
        )

        # Add method to processor method list.
        rpc_method = RPCMethod(
            function=function,
            metadata=metadata,
            depends=depends,
            params_model=param_model,
            params_schema_model=param_schema_model,
            result_model=result_model,
            required=required,
        )
        self._rpc_methods[metadata.name] = rpc_method
        log.debug(
            "Registering function [%s] as method [%s]", function.__name__, metadata.name
        )
        self._request_processor.method(rpc_method, metadata.name)
        return function
