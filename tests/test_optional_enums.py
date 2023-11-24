"""Test discovering enums in union fields."""
import enum
from typing import Optional

from pydantic import BaseModel

from openrpc import OpenRPC, RPCServer


class TestEnum(enum.Enum):
    """Enum for testing."""

    VALUE = 1


class Model(BaseModel):
    enum_field: Optional[TestEnum]


rpc = RPCServer(debug=True)


@rpc.method()
def method() -> Model:
    """Method returning model with optional enum field."""


def test_nested_enum_discover() -> None:
    discover = OpenRPC(**rpc.discover())
    assert discover.components.schemas["TestEnum"].title == "TestEnum"
