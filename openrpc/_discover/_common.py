"""Shared components for discover modules."""
from typing import Type, TypeVar

from pydantic import BaseModel

Model = TypeVar("Model", bound=BaseModel)
ModelType = Type[Model]
