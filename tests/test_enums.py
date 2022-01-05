"""Test Python enums to JSON Schema enums."""
import unittest
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    """Example type for the enum."""

    int_field: int


class EnumExample(Enum):
    """Each type for options should get a JSON Schema type."""

    int_option: int = 3
    str_option: str = 'A string with a "'


# TODO Determine if JSON Schema spec supports non-primitive enum values.
class EnumClassFieldExample(Enum):
    """Enum with a field of a custom class type."""

    class_option: Model


class EnumUnsetExample(Enum):
    """Enum with a field of a custom class type."""

    no_value: float


class EnumExampleWithNullable(Enum):
    """If any field is nullable "null" should be a valid type."""

    str_option: str = r'\"\\"'
    opt_int_option: Optional[int] = None


class EnumTest(unittest.TestCase):
    pass
