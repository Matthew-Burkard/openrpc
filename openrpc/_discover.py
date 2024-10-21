"""Module for `rpc.discover` related functions."""

__all__ = ("get_openrpc_doc",)

import re
from typing import Any, Iterable, Optional, Union

import lorem_pysum
from pydantic import create_model


from openrpc._common import RPCMethod, get_schema
from openrpc._objects import (
    Components,
    ContentDescriptor,
    Example,
    ExamplePairing,
    Info,
    Method,
    OpenRPC,
    Schema,
    SchemaType,
    Server,
)

COMPONENTS_REF = "#/components/schemas/"
REF_TEMPLATE = f"{COMPONENTS_REF}{{model}}"

param_pattern = re.compile(r" *:param (.*?): (.*?)(?=:\w|$)")
return_pattern = re.compile(r" *:return: (.*?)(?=:\w|$)")


def get_openrpc_doc(
    info: Info, rpc_methods: Iterable[RPCMethod], servers: Union[list[Server], Server]
) -> OpenRPC:
    """Get an Open RPC document describing the RPC server.

    :param info: RPC server info.
    :param rpc_methods: RPC server methods.
    :param servers: Servers hosting this RPC API.
    :return: The OpenRPC doc for the given server.
    """
    fields: dict[str, Any] = {}
    for method in rpc_methods:
        if method.metadata.name == "rpc.discover":
            continue
        fields[method.metadata.name + ".params"] = (method.params_schema_model, None)
        fields[method.metadata.name + ".result"] = (method.result_model, None)
    rpc_api_model = create_model("OpenRPCAPIModel", **fields)
    api_schema = Schema(**rpc_api_model.model_json_schema(ref_template=REF_TEMPLATE))

    methods = get_methods(rpc_methods, api_schema)
    return OpenRPC(
        openrpc="1.2.6",
        info=info,
        components=Components(schemas=api_schema.defs or {}),
        methods=methods,
        servers=servers,
    )


def get_methods(rpc_methods: Iterable[RPCMethod], api_schema: Schema) -> list[Method]:
    """Get OpenRPC method objects.

    :param rpc_methods: Decorated functions data.
    :return: OpenRPC method objects.
    """
    methods: list[Method] = []
    for rpc_method in rpc_methods:
        if rpc_method.metadata.name == "rpc.discover":
            continue
        method = Method(
            name=rpc_method.metadata.name,
            params=_get_params(rpc_method, api_schema),
            result=_get_result(rpc_method, api_schema),
            examples=rpc_method.metadata.examples or [_get_example(rpc_method)],
        )
        # Delete param and result schemas.
        # Their values have been pulled out.
        api_schema.defs = api_schema.defs or {}
        if (ref := f"{rpc_method.metadata.name}_result") in api_schema.defs:
            del api_schema.defs[ref]
            del api_schema.defs[f"{rpc_method.metadata.name}_params"]
        # Don't pass `None` values to constructor for sake of
        # `exclude_unset` in discover.
        if rpc_method.metadata.tags is not None:
            method.tags = rpc_method.metadata.tags
        if (summary := _get_summary(rpc_method)) is not None:
            method.summary = summary
        if (description := _get_description(rpc_method)) is not None:
            method.description = description
        if rpc_method.metadata.external_docs is not None:
            method.external_docs = rpc_method.metadata.external_docs
        if rpc_method.metadata.deprecated is not None:
            method.deprecated = rpc_method.metadata.deprecated
        if rpc_method.metadata.servers is not None:
            method.servers = rpc_method.metadata.servers
        if rpc_method.metadata.errors is not None:
            method.errors = rpc_method.metadata.errors
        if rpc_method.metadata.links is not None:
            method.links = rpc_method.metadata.links
        if rpc_method.metadata.param_structure is not None:
            method.param_structure = rpc_method.metadata.param_structure
        method.x_security = rpc_method.metadata.security
        methods.append(method)
    return methods


def _get_result(rpc_method: RPCMethod, api_schema: Schema) -> ContentDescriptor:
    if rpc_method.metadata.result:
        return rpc_method.metadata.result
    properties = _get_schemas(f"{rpc_method.metadata.name}.result", api_schema)
    schema = properties["result"]
    descriptor = ContentDescriptor(name="result", schema=schema)
    result_description = re.findall(
        return_pattern, re.sub(r"\n +", " ", rpc_method.function.__doc__ or "")
    )
    if result_description:
        descriptor.description = result_description[0].strip()
    return descriptor


def _get_params(rpc_method: RPCMethod, api_schema: Schema) -> list[ContentDescriptor]:
    if rpc_method.metadata.params:
        return rpc_method.metadata.params
    # Find param descriptions.
    param_descriptions = {
        group[0]: group[1].strip()
        for group in re.findall(
            param_pattern, re.sub(r"\n +", " ", rpc_method.function.__doc__ or "")
        )
    }
    descriptors: list[ContentDescriptor] = []
    # Get schema for each param.
    properties = _get_schemas(f"{rpc_method.metadata.name}.params", api_schema)
    for name in rpc_method.params_schema_model.model_fields:
        descriptor = ContentDescriptor(
            name=name,
            schema=properties[name],
            required=name in rpc_method.required,
        )
        if description := param_descriptions.get(name):
            descriptor.description = description
        descriptors.append(descriptor)
    return descriptors


def _get_schemas(api_property_name: str, api_schema: Schema) -> dict[str, SchemaType]:
    properties = api_schema.properties or {}
    ref_schema = get_schema(properties.pop(api_property_name))
    ref = (ref_schema.ref or "").replace(COMPONENTS_REF, "")
    defs = api_schema.defs or {}
    schema = get_schema(defs.get(ref))
    return schema.properties or {}


def _get_example(rpc_method: RPCMethod) -> ExamplePairing:
    param_values = lorem_pysum.generate(
        rpc_method.params_schema_model, explicit_default=True
    )
    params = [
        Example(name=name, value=getattr(param_values, name))
        for name in param_values.model_fields
    ]
    result_value = lorem_pysum.generate(rpc_method.result_model, explicit_default=True)
    result = Example(value=result_value.result)  # type: ignore

    return ExamplePairing(params=params, result=result)


def _get_summary(rpc_method: RPCMethod) -> Optional[str]:
    summary = rpc_method.metadata.summary
    if not summary:
        summary = rpc_method.function.__doc__
        # If using function doc as summary only take intro line.
        if summary:
            summary = summary.split("\n")[0].strip()
    return summary


def _get_description(rpc_method: RPCMethod) -> Optional[str]:
    description = rpc_method.metadata.description
    if not description and (
        (doc_string := rpc_method.function.__doc__)
        and (match := re.match(r"^.*?\n\n(.*?)(\n\n|$)", doc_string, re.S))
    ):
        doc = re.sub(r"\s+", " ", match.groups()[0]).strip()
        if not doc.startswith(":"):
            return doc
    return description
