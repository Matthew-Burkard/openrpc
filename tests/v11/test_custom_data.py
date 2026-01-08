"""Test custom method metadata."""

from openrpc import ContentDescriptor, OpenRPC, RPCApp

rpc = RPCApp()


@rpc.method(
    params=[ContentDescriptor(name="a.b", schema=True)],
    result=ContentDescriptor(name="a.b", schema=True),
)
def custom_method() -> None:
    pass


def test_custom_metadata() -> None:
    doc = OpenRPC(**rpc.discover())
    method = doc.methods[0]
    param = method.params[0]
    assert param.name == "a.b"
    assert method.params[0].schema_ is True
    assert method.result.schema_ is True
