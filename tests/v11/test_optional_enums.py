"""Test discovering enums in union fields."""

import enum
from typing import Optional

from pydantic import BaseModel

from openrpc import OpenRPC
from openrpc._objects import Schema
from openrpc.app import RPCApp


class SomeEnum(enum.Enum):
    """Enum for testing."""

    VALUE = 1


class Model(BaseModel):
    enum_field: Optional[SomeEnum]


rpc = RPCApp(debug=True)


@rpc.method()
def method() -> Model:  # pyright: ignore[reportReturnType]
    """Method returning model with optional enum field."""


def test_nested_enum_discover() -> None:
    discover = OpenRPC(**rpc.discover())
    assert discover.components is not None
    assert discover.components.schemas is not None
    schema = discover.components.schemas["SomeEnum"]
    assert isinstance(schema, Schema)
    assert schema.title == "SomeEnum"
    assert schema.enum == [1]
