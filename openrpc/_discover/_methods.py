"""Module for generating OpenRPC document methods."""
__all__ = ("get_methods",)

from typing import get_args, Iterable, Optional

import lorem_pysum
from pydantic_core import PydanticUndefined

from openrpc import ContentDescriptor, Example, ExamplePairing, Method, Schema
from openrpc._common import RPCMethod

NoneType = type(None)


def get_methods(rpc_methods: Iterable[RPCMethod]) -> list[Method]:
    """Get OpenRPC method objects.

    :param rpc_methods: Decorated functions data.
    :return: OpenRPC method objects.
    """
    methods = []
    for m in rpc_methods:
        if m.metadata.name == "rpc.discover":
            continue
        method = Method(
            name=m.metadata.name or m.function.__name__,
            params=m.metadata.params or _get_params(m),
            result=m.metadata.result or _get_result(m),
            examples=m.metadata.examples or [_get_example(m)],
        )
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if m.metadata.tags is not None:
            method.tags = m.metadata.tags
        if m.metadata.summary is not None:
            method.summary = m.metadata.summary
        if (description := _get_description(m)) is not None:
            method.description = description
        if m.metadata.external_docs is not None:
            method.external_docs = m.metadata.external_docs
        if m.metadata.deprecated is not None:
            method.deprecated = m.metadata.deprecated
        if m.metadata.servers is not None:
            method.servers = m.metadata.servers
        if m.metadata.errors is not None:
            method.errors = m.metadata.errors
        if m.metadata.links is not None:
            method.links = m.metadata.links
        if m.metadata.param_structure is not None:
            method.param_structure = m.metadata.param_structure
        if m.metadata.security is not None:
            method.x_security = m.metadata.security
        methods.append(method)
    return methods


def _get_result(rpc_method: RPCMethod) -> ContentDescriptor:
    result_field = rpc_method.result_model.model_fields["result"]
    return ContentDescriptor(
        name="result",
        schema=rpc_method.result_model.model_json_schema()["properties"]["result"],
        required=NoneType not in get_args(result_field),
    )


def _get_params(rpc_method: RPCMethod) -> list[ContentDescriptor]:
    return [
        ContentDescriptor(
            name=name,
            schema=Schema(
                **rpc_method.params_model.model_json_schema()["properties"][name]
            ),
            required=field.default is PydanticUndefined,
        )
        for name, field in rpc_method.params_model.model_fields.items()
    ]


def _get_example(rpc_method: RPCMethod) -> ExamplePairing:
    param_values = lorem_pysum.generate(rpc_method.params_model, explicit_default=True)
    params = [
        Example(name=name, value=getattr(param_values, name))
        for name in param_values.model_fields
    ]
    result_value = lorem_pysum.generate(rpc_method.result_model, explicit_default=True)
    result = Example(value=result_value.result)  # type: ignore

    return ExamplePairing(params=params, result=result)


def _get_description(rpc_method: RPCMethod) -> Optional[str]:
    description = rpc_method.metadata.description
    if not description:
        description = rpc_method.function.__doc__
        # If using function doc as description only take intro line.
        if description:
            description = description.split("\n")[0]
    return description
