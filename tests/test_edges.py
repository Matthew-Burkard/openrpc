"""Misc unit tests."""

import json

from openrpc import RPCServer
from tests.util import Vector3

rpc = RPCServer(debug=True)


@rpc.method()
def get_distance(a: Vector3, b: Vector3) -> Vector3:
    """Get distance between two points in 3D space."""
    return Vector3(x=a.x - b.x, y=a.y - b.y, z=a.z - b.z)


def test_model_para_by_name() -> None:
    params = '{"a": {"x": 1, "y": 1, "z": 1}, "b": {"x": 1, "y": 1, "z": 1}}'
    req = '{"id": 1, "method": "get_distance", "params": %s, "jsonrpc": "2.0"}' % params
    resp = rpc.process_request(req) or ""
    assert json.loads(resp)["result"] == {"x": 0, "y": 0, "z": 0}
