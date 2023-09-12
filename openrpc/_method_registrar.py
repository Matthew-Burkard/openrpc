"""Module providing method registrar interface."""

__all__ = ("MethodRegistrar", "CallableType")

import inspect
import logging
import warnings
from functools import partial
from typing import Callable, Optional, TypeVar, Union

from pydantic import create_model

from openrpc import Depends
from openrpc._common import MethodMetaData, resolved_annotation, RPCMethod
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
DecoratedCallableType = TypeVar("DecoratedCallableType", bound=Callable)


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
        *args: CallableType,
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
    ) -> Union[CallableType, Callable[[DecoratedCallableType], DecoratedCallableType]]:
        """Register a method with this OpenRPC server.

        :param args: The method if this is used as a plain decorator.
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
        if not args:
            self._warn = False
            return partial(  # type: ignore
                self.method,
                name=name,
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
                security=security,
            )
        if self._warn:
            warnings.warn(
                "RPCServer `method` decorator must be called in future releases, use"
                " `method()` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        self._warn = True
        func = args[0]
        name = name or func.__name__
        return self._method(
            func,
            MethodMetaData(
                name=name,
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

    def remove(self, method: str) -> None:
        """Remove a method from this server by name.

        :param method: Name of the method to remove.
        :return: None.
        """
        self._rpc_methods.pop(method)
        self._request_processor.methods.pop(method)

    def _method(self, function: CallableType, metadata: MethodMetaData) -> CallableType:
        signature = inspect.signature(function)
        depends = [k for k, v in signature.parameters.items() if v.default is Depends]

        # Params model.
        param_model = create_model(  # type: ignore
            f"{metadata.name}Params",
            **{
                k: (
                    resolved_annotation(v.annotation, function),
                    v.default if v.default is not inspect.Signature.empty else ...,
                )
                for k, v in signature.parameters.items()
                if k not in depends and not k.startswith("_")
            },
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
            depends_params=depends,
            params_model=param_model,
            result_model=result_model,
        )
        self._rpc_methods[metadata.name] = rpc_method
        log.debug(
            "Registering function [%s] as method [%s]", function.__name__, metadata.name
        )
        self._request_processor.method(rpc_method, metadata.name)
        return function
