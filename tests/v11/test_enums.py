"""Test Python enums to JSON Schema enums."""

import enum
import json
from typing import Optional

import pytest

from openrpc import Info, OpenRPC, RPCApp
from tests.util import resolve
from tests.v11 import util

rpc = RPCApp(Info(title="Test Enums", version="1.0.0"), debug=True)


class EnumExample(enum.Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


class EnumExampleWithNull(enum.Enum):
    """If any field is None, "null" should be a valid type."""

    STR_OPTION = r'\"\\"'
    OPT_INT_OPTION = None


@rpc.method()
def enum_test_func(ee: EnumExample) -> EnumExampleWithNull:
    """Function with Enum param and result."""
    assert isinstance(ee, EnumExample)
    return EnumExampleWithNull.STR_OPTION


@pytest.mark.asyncio
async def test_register_enum_using_method() -> None:
    rpc_doc = rpc.discover()
    schemas = rpc_doc["components"]["schemas"]
    methods = rpc_doc["methods"]

    # Param expectations.
    param_schema = {
        "description": "Each type for options should get a JSON Schema type.",
        "enum": [3, 'A string with a "'],
        "title": "EnumExample",
    }
    # Result expectations.
    result_schema = {
        "description": 'If any field is None, "null" should be a valid type.',
        "enum": ['\\"\\\\"', None],
        "title": "EnumExampleWithNull",
    }

    ref: str = methods[0]["params"][0][  # pyright: ignore[reportRedeclaration]
        "schema"
    ]["$ref"]
    assert schemas[ref.removeprefix("#/components/schemas/")] == param_schema

    ref: str = methods[0]["result"]["schema"]["$ref"]
    assert schemas[ref.removeprefix("#/components/schemas/")] == result_schema


@pytest.mark.asyncio
async def test_calling_enums_method() -> None:
    result = await util.get_result(rpc, enum_test_func, [3])
    assert result == EnumExampleWithNull.STR_OPTION.value


@pytest.mark.asyncio
async def test_calling_enums_method_with_bar_param() -> None:
    result = await util.get_result(rpc, enum_test_func, [5])
    assert (
        result["error"]["data"].split("\n")[0]
        == "1 validation error for enum_test_func.params"
    )


@pytest.mark.asyncio
async def test_enum_optional_param() -> None:
    e_rpc = RPCApp(debug=True)

    class EnumOnlyUsedAsParam(enum.Enum):
        """Enum only ever used as a parameter type."""

        OPTION = enum.auto()

    @e_rpc.method()
    def method(  # pyright: ignore[reportUnusedFunction]
        param: Optional[EnumOnlyUsedAsParam],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Pass."""

    req = util.req_str("rpc.discover")
    response = json.loads((await e_rpc.process(req)) or "")
    doc = OpenRPC(**response["result"])

    param_schema = doc.methods[0].params[0].schema_
    assert not isinstance(param_schema, bool)
    assert param_schema.any_of is not None

    enum_ref = param_schema.any_of[0]
    enum_schema = resolve(enum_ref, doc.components)
    assert enum_schema.enum == [1]

    none_schema = param_schema.any_of[1]
    assert not isinstance(none_schema, bool)
    assert none_schema.type == "null"
