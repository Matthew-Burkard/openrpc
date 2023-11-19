"""Module providing class to handle middleware dependencies."""
from typing import Callable

from pydantic import BaseModel


class DependsModel(BaseModel):
    """Supply with function used to return a dependent argument."""

    function: Callable


def _depends(function: Callable) -> DependsModel:
    return DependsModel(function=function)


Depends = _depends
