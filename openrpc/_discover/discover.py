"""Module for `rpc.discover` related functions."""

__all__ = ("get_openrpc_doc",)

import json
from typing import Iterable

from openrpc import Components, Info, OpenRPC
from openrpc._common import RPCMethod
from openrpc._discover._methods import get_methods
from openrpc._discover._schemas import get_type_to_schema_map


def get_openrpc_doc(info: Info, rpc_methods: Iterable[RPCMethod]) -> OpenRPC:
    """Get an Open RPC document describing the RPC server.

    :param info: RPC server info.
    :param rpc_methods: RPC server methods.
    :return: The OpenRPC doc for the given server.
    """
    type_schema_map = get_type_to_schema_map(
        [rpc for rpc in rpc_methods if rpc.metadata.name != "rpc.discover"]
    )
    components = Components(
        schemas={v.title or "": v for v in type_schema_map.values()}
    )

    return OpenRPC(
        **json.loads(
            OpenRPC(
                openrpc="1.2.6",
                info=info,
                methods=get_methods(rpc_methods),
                components=components,
            ).model_dump_json(by_alias=True, exclude_unset=True)
            # Workaround to OpenRPC playground bug resolving definitions.
            .replace("#/$defs/", "#/components/schemas/")
        )
    )
