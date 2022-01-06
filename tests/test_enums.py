"""Test Python enums to JSON Schema enums."""
import unittest
from enum import Enum

from pydantic import BaseModel


class Model(BaseModel):
    """Example type for the enum."""

    int_field: int


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION = 3
    STR_OPTION = 'A string with a "'


# TODO Determine if JSON Schema spec supports non-primitive enum values.
class EnumClassFieldExample(Enum):
    """Enum with a field of a custom class type."""

    CLASS_OPTION = Model(int_field=1)


class EnumExampleWithNull(Enum):
    """If any field is null "null" should be a valid type."""

    STR_OPTION = r'\"\\"'
    OPT_INT_OPTION = None


# noinspection PyMissingOrEmptyDocstring
def coffee(ee: EnumExample, ecf: EnumClassFieldExample) -> EnumExampleWithNull:
    return EnumExampleWithNull.STR_OPTION


class EnumTest(unittest.TestCase):
    def test_register_enum_using_method(self) -> None:
        pass
