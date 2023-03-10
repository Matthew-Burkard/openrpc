"""Module providing method registrar interface."""
import inspect
import logging
from functools import partial
from typing import Callable, Optional, TypeVar, Union

from openrpc import Depends
from openrpc._method_processor import MethodProcessor
from openrpc._objects import (
    ContentDescriptorObject,
    ErrorObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    LinkObject,
    ParamStructure,
    ServerObject,
    TagObject,
)
from openrpc._rpcmethod import MethodMetaData, RPCMethod

__all__ = ("MethodRegistrar", "CallableType")


log = logging.getLogger("openrpc")

CallableType = TypeVar("CallableType", bound=Callable)
DecoratedCallableType = TypeVar("DecoratedCallableType", bound=Callable)


class MethodRegistrar:
    """Interface for registering RPC methods."""

    def __init__(self) -> None:
        """Initialize a new instance of the MethodRegistrar class."""
        self._rpc_methods: dict[str, RPCMethod] = {}
        self._method_processor = MethodProcessor()

    def method(
        self,
        *args: CallableType,
        name: Optional[str] = None,
        params: Optional[list[ContentDescriptorObject]] = None,
        result: Optional[ContentDescriptorObject] = None,
        tags: Optional[list[Union[TagObject, str]]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        external_docs: Optional[ExternalDocumentationObject] = None,
        deprecated: Optional[bool] = None,
        servers: Optional[list[ServerObject]] = None,
        errors: Optional[list[ErrorObject]] = None,
        links: Optional[list[LinkObject]] = None,
        param_structure: Optional[ParamStructure] = None,
        examples: Optional[list[ExamplePairingObject]] = None,
    ) -> Union[CallableType, Callable[[DecoratedCallableType], DecoratedCallableType]]:
        """Register a method with this OpenRPC server.

        Can be used as a plain decorator, eg:

        .. code-block:: python

            @method
            def my_func()

        Or additional method info can be provided with a MethodObject:

        .. code-block:: python

            @method(name="dot.case.method", deprecated=True)
            def my_func()

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
        :return: The method decorator.
        """
        tag_objects = (
            [tag if isinstance(tag, TagObject) else TagObject(name=tag) for tag in tags]
            if tags is not None
            else None
        )
        if not args:
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
            )
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
            ),
        )

    def remove(self, method: str) -> None:
        """Remove a method from this server by name.

        :param method: Name of the method to remove.
        :return: None.
        """
        self._rpc_methods.pop(method)
        self._method_processor.methods.pop(method)

    def _method(self, func: CallableType, metadata: MethodMetaData) -> CallableType:
        dependencies = [
            k
            for k, v in inspect.signature(func).parameters.items()
            if v.default is Depends
        ]
        rpc_method = RPCMethod(
            function=func, metadata=metadata, depends_params=dependencies
        )
        self._rpc_methods[metadata.name] = rpc_method
        log.debug(
            "Registering function [%s] as method [%s]", func.__name__, metadata.name
        )
        self._method_processor.method(rpc_method, metadata.name)
        return func