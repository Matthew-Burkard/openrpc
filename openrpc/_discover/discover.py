"""Module for `rpc.discover` related functions."""

__all__ = ("get_openrpc_doc",)

import json
from typing import Iterable

from openrpc import ComponentsObject, InfoObject, OpenRPCObject
from openrpc._discover._methods import get_methods
from openrpc._discover._schemas import get_type_to_schema_map
from openrpc._rpcmethod import RPCMethod


def get_openrpc_doc(
    info: InfoObject, rpc_methods: Iterable[RPCMethod]
) -> OpenRPCObject:
    """Get an Open RPC document describing the RPC server.

    :param info: RPC server info.
    :param rpc_methods: RPC server methods.
    :return: The Open-RPC doc for the given server.
    """
    type_schema_map = get_type_to_schema_map([rpc.function for rpc in rpc_methods])
    components = ComponentsObject(
        schemas={v.title or "": v for v in type_schema_map.values()}
    )

    return OpenRPCObject(
        **json.loads(
            OpenRPCObject(
                openrpc="1.2.6",
                info=info,
                methods=get_methods(rpc_methods, type_schema_map),
                components=components,
            ).model_dump_json(by_alias=True, exclude_unset=True)
            # Workaround to Open-RPC playground bug resolving definitions.
            .replace("#/$defs/", "#/components/schemas/")
        )
    )
