"""Module for `rpc.discover` related functions.

This is iteration number 3 of this module and I'm still unhappy with it.
"""

__all__ = ("get_openrpc_doc",)

import re
from typing import Any, Iterable, Optional, Union

import lorem_pysum


from openrpc._common import RPCMethod
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

schema_ref = "#/components/schemas"
param_pattern = re.compile(r" *:param (.*?): (.*?)(?=:\w|$)")
return_pattern = re.compile(r" *:return: (.*?)(?=:\w|$)")


def get_openrpc_doc(
    info: Info, rpc_methods: Iterable[RPCMethod], servers: Union[list[Server], Server]
) -> OpenRPC:
    """Get an Open RPC document describing the RPC server.

    :param info: RPC server info.
    :param rpc_methods: RPC server methods.
    :param servers: Servers hosting this RPC APi.
    :return: The OpenRPC doc for the given server.
    """
    methods, schemas = get_methods(rpc_methods)
    return OpenRPC(
        openrpc="1.2.6",
        info=info,
        components=Components(schemas=schemas),
        methods=methods,
        servers=servers,
    )


def get_methods(
    rpc_methods: Iterable[RPCMethod],
) -> tuple[list[Method], dict[str, SchemaType]]:
    """Get OpenRPC method objects.

    :param rpc_methods: Decorated functions data.
    :return: OpenRPC method objects.
    """
    schemas: dict[str, SchemaType] = {}
    methods: list[Method] = []
    for rpc_method in rpc_methods:
        if rpc_method.metadata.name == "rpc.discover":
            continue
        params_schema = Schema(**rpc_method.params_model.model_json_schema())
        param_ref = params_schema.title or ""
        schemas = flatten_schemas(param_ref, param_ref, params_schema, schemas)
        result_schema = Schema(**rpc_method.result_model.model_json_schema())
        result_ref = result_schema.title or ""
        schemas = flatten_schemas(result_ref, result_ref, result_schema, schemas)

        method = Method(
            name=rpc_method.metadata.name or rpc_method.function.__name__,
            params=_get_params(rpc_method, schemas),
            result=_get_result(rpc_method, schemas),
            examples=rpc_method.metadata.examples or [_get_example(rpc_method)],
        )
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
    return methods, schemas


def flatten_schemas(
    base_ref: str, ref: str, schema: Schema, schemas: dict[str, SchemaType]
) -> dict[str, SchemaType]:
    # Handle schema lists.
    for attr, schema_list in [
        ("all_of", schema.all_of or []),
        ("any_of", schema.any_of or []),
        ("one_of", schema.one_of or []),
        ("prefix_items", schema.prefix_items or []),
    ]:
        new_list: list[SchemaType] = []
        for index, schema_item in enumerate(schema_list or []):
            if isinstance(schema_item, bool) or schema_item.is_primitive():
                new_list.append(schema_item)
                continue
            new_ref = f"{ref}.{attr}.{index}"
            new_schema, schemas = _handle_schema(
                base_ref, new_ref, schema_item, schemas
            )
            new_list.append(new_schema)
        if new_list:
            setattr(schema, attr, new_list)

    # Handle schema maps.
    for attr, schema_map in [
        ("properties", schema.properties or {}),
        ("pattern_properties", schema.pattern_properties or {}),
        ("dependent_schemas", schema.dependent_schemas or {}),
        ("defs", schema.defs or {}),
    ]:
        new_map: dict[str, SchemaType] = {}
        for name, schema_item in schema_map.items():
            if isinstance(schema_item, bool) or schema_item.is_primitive():
                new_map[name] = schema_item
                continue
            new_ref = f"{ref}.{attr}.{name}"
            new_schema, schemas = _handle_schema(
                base_ref, new_ref, schema_item, schemas
            )
            new_map[name] = new_schema
        if new_map:
            setattr(schema, attr, new_map)

    # Handle schemas.
    for attr in ("not_", "property_names", "items", "contains", "if_", "then", "else_"):
        schema_item: Optional[SchemaType] = getattr(schema, attr)
        if (
            schema_item is None
            or isinstance(schema_item, bool)
            or schema_item.is_primitive()
        ):
            continue
        new_ref = f"{ref}.{attr}"
        new_schema, schemas = _handle_schema(base_ref, new_ref, schema_item, schemas)
        setattr(schema, attr, new_schema)

    schemas[ref] = schema
    return schemas


def _handle_schema(
    base_ref: str, ref: str, schema: Schema, schemas: dict[str, SchemaType]
) -> tuple[Schema, dict[str, SchemaType]]:
    if schema.ref is not None:
        schema.ref = schema.ref.replace("#/$defs/", f"{schema_ref}/{base_ref}.defs.")
        return schema, schemas
    schemas = flatten_schemas(base_ref, ref, schema, schemas)
    data: Any = {"$ref": f"{schema_ref}/{ref}"}
    return Schema(**data), schemas


def _get_result(
    rpc_method: RPCMethod, schemas: dict[str, SchemaType]
) -> ContentDescriptor:
    if rpc_method.metadata.result:
        return rpc_method.metadata.result
    result_schema = schemas.pop(rpc_method.result_model.__name__)
    if isinstance(result_schema, bool):
        schema = result_schema
    else:
        properties = result_schema.properties
        schema = True if properties is None else properties["result"]
    descriptor = ContentDescriptor(name="result", schema=schema)
    result_description = re.findall(
        return_pattern, re.sub(r"\n +", " ", rpc_method.function.__doc__ or "")
    )
    if result_description:
        descriptor.description = result_description[0].strip()
    return descriptor


def _get_params(
    rpc_method: RPCMethod, schemas: dict[str, SchemaType]
) -> list[ContentDescriptor]:
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
    schema = schemas.pop(f"{rpc_method.params_model.__name__}")
    if isinstance(schema, bool):
        return []
    # Get schema for each param.
    properties = schema.properties or {}
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
