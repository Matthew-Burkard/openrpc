"""Functions shared by tests."""

import json
from typing import Any, Optional, Union

from jsonrpcobjects.objects import ErrorResponse, ResponseType, ResultResponse
from pydantic import BaseModel

from openrpc import RPCServer
from openrpc._objects import Components, Schema, SchemaType

INTERNAL_ERROR = -32603
INVALID_PARAMS = -32602
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
PARSE_ERROR = -32700
SERVER_ERROR = -32000


class Vector3(BaseModel):
    """x, y, and z values."""

    x: float
    y: float
    z: float


def parse_response(data: Union[bytes, str, None]) -> ResponseType:
    """Map a JSON-RPC2 response to the appropriate object."""
    resp = json.loads(data or "")
    if resp.get("error"):
        return ErrorResponse(**resp)
    return ResultResponse(**resp)


def parse_result_response(data: Union[bytes, str, None]) -> ResultResponse:
    """Map a JSON-RPC2 response to ResultResponse."""
    resp = json.loads(data or "")
    return ResultResponse(**resp)


def parse_error_response(data: Union[bytes, str, None]) -> ErrorResponse:
    """Map a JSON-RPC2 response to ErrorResponse."""
    resp = json.loads(data or "")
    return ErrorResponse(**resp)


def get_response(
    rpc: RPCServer, request: str, middleware_args: Optional[Any] = None
) -> dict[str, Any]:
    """Process request asserting that there is a `str` response."""
    resp = rpc.process_request(request, middleware_args)
    assert resp is not None
    return json.loads(resp)


async def get_response_async(
    rpc: RPCServer, request: str, middleware_args: Optional[Any] = None
) -> dict[str, Any]:
    """Process request asserting that there is a `str` response."""
    resp = await rpc.process_request_async(request, middleware_args)
    assert resp is not None
    return json.loads(resp)


def get_request(method: str, params: Optional[Any] = None) -> str:
    """Get a request string."""
    if params is None:
        return f'{{"id": 1, "method": "{method}", "jsonrpc": "2.0"}}'
    return f'{{"id": 1, "method": "{method}", "params": {params}, "jsonrpc": "2.0"}}'


def resolve(ref: Optional[SchemaType], components: Optional[Components]) -> Schema:
    assert ref is not None
    assert components is not None
    assert components.schemas is not None
    assert not isinstance(ref, bool)
    assert ref.ref is not None
    schema = components.schemas[ref.ref.removeprefix("#/components/schemas/")]
    assert not isinstance(schema, bool)
    return schema


def dump(model: Union[BaseModel, bool]) -> dict[str, Any]:  # noqa: FBT001
    assert not isinstance(model, bool)
    return model.model_dump(exclude_unset=True, by_alias=True)


def validate_references(
    schema: Optional[SchemaType],
    components: Optional[Components],
    processed: Optional[list[str]] = None,
) -> None:
    if schema is None or isinstance(schema, bool):
        return
    assert components is not None
    processed = processed or []
    if schema.ref in processed:
        return
    if schema.ref:
        processed.append(schema.ref)
        ref_schema = components.resolve_reference(schema.ref)
        validate_references(ref_schema, components, processed)
    schema_item: Optional[SchemaType] = None  # pyright: ignore[reportRedeclaration]
    for attr in ["any_of", "all_of", "one_of", "prefix_items"]:
        schema_list: list[SchemaType] = getattr(schema, attr) or []
        for schema_item in schema_list:
            validate_references(schema_item, components, processed)
    for attr in ["properties", "pattern_properties", "dependent_schemas", "defs"]:
        schema_maps: dict[str, SchemaType] = getattr(schema, attr) or {}
        for schema_item in schema_maps.values():
            validate_references(schema_item, components, processed)
    for attr in ("not_", "property_names", "items", "contains", "if_", "then", "else_"):
        schema_item: Optional[SchemaType] = getattr(schema, attr)
        validate_references(schema_item, components, processed)
