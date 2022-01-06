"""Test Python enums to JSON Schema enums."""
import unittest
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    """Example type for the enum."""

    INT_FIELD: int


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    INT_OPTION: int = 3
    STR_OPTION: str = 'A string with a "'


# TODO Determine if JSON Schema spec supports non-primitive enum values.
class EnumClassFieldExample(Enum):
    """Enum with a field of a custom class type."""

    CLASS_OPTION: Model


class EnumUnsetExample(Enum):
    """Enum with a field of a custom class type."""

    NO_VALUE: float


class EnumExampleWithNullable(Enum):
    """If any field is nullable "null" should be a valid type."""

    STR_OPTION: str = r'\"\\"'
    OPT_INT_OPTION: Optional[int] = None


class EnumTest(unittest.TestCase):
    def test_register_enum_using_method(self) -> None:
        pass
