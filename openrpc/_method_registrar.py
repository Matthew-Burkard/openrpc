"""Module providing method registrar interface."""
import logging
from functools import partial
from typing import Callable, Optional, TypeVar, Union

from openrpc import ContentDescriptorObject
from openrpc._method_processor import MethodProcessor
from openrpc._objects import (
    ErrorObject,
    ExamplePairingObject,
    ExternalDocumentationObject,
    LinkObject,
    ParamStructure,
    ServerObject,
    TagObject,
)
from openrpc._util import Function

__all__ = ("MethodRegistrar",)

log = logging.getLogger("openrpc")

CallableType = TypeVar("CallableType", bound=Callable)
DecoratedCallableType = TypeVar("DecoratedCallableType", bound=Callable)


class MethodRegistrar:
    """Interface for registering RPC methods."""

    def __init__(self) -> None:
        """Initialize a new instance of the MethodRegistrar class."""
        self._functions: dict[str, Function] = {}
        self._method_processor = MethodProcessor()

    def method(
        self,
        *args: CallableType,
        name: Optional[str] = None,
        params: Optional[list[ContentDescriptorObject]] = None,
        result: Optional[ContentDescriptorObject] = None,
        tags: Optional[list[TagObject]] = None,
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
        metadata = {
            "name": name,
            "params": params,
            "result": result,
            "tags": tags,
            "summary": summary,
            "description": description,
            "externalDocs": external_docs,
            "deprecated": deprecated,
            "servers": servers,
            "errors": errors,
            "links": links,
            "paramStructure": param_structure,
            "examples": examples,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        if args:
            func = args[0]
        else:
            return partial(self.method, **metadata)  # type: ignore
        name = name or func.__name__
        metadata["name"] = name
        self._functions[name] = Function(function=func, metadata=metadata)
        log.debug("Registering method [%s]", func.__name__)
        return self._method_processor.method(func, name)

    def remove(self, method: str) -> None:
        """Remove a method from this server by name.

        :param method: Name of the method to remove.
        :return: None.
        """
        self._functions.pop(method)
