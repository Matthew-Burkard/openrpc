"""Misc unit tests."""

import json

from openrpc import RPCServer
from openrpc._objects import OpenRPC, Schema
from tests.util import Vector3

rpc = RPCServer(debug=True)


@rpc.method()
def get_distance(a: Vector3, b: Vector3) -> Vector3:
    """Get distance between two points in 3D space."""
    return Vector3(x=a.x - b.x, y=a.y - b.y, z=a.z - b.z)


def test_model_param_by_name() -> None:
    params = '{"a": {"x": 1, "y": 1, "z": 1}, "b": {"x": 1, "y": 1, "z": 1}}'
    req = '{"id": 1, "method": "get_distance", "params": %s, "jsonrpc": "2.0"}' % params
    resp = rpc.process_request(req) or ""
    assert json.loads(resp)["result"] == {"x": 0, "y": 0, "z": 0}


def test_resolve_reference() -> None:
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    ref_schema = method.params[0].schema_
    assert isinstance(ref_schema, Schema)
    assert ref_schema.ref is not None
    assert doc.components is not None
    schema = doc.components.resolve_reference(ref_schema.ref)
    assert schema is not None
    assert isinstance(schema, Schema)
    doc.components.schemas = None
    assert doc.components.resolve_reference(ref_schema.ref) is None
