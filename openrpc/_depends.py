"""Module providing class to handle middleware dependencies."""
import inspect
from typing import Any, Callable

from pydantic import BaseModel


class DependsModel(BaseModel):
    """Supply with function used to return a dependent argument."""

    function: Callable
    depends_params: dict[str, "DependsModel"]
    accepts_caller_details: bool


def _depends(function: Callable) -> Any:
    signature = inspect.signature(function)
    depends_params = {
        k: v.default
        for k, v in signature.parameters.items()
        if isinstance(v.default, DependsModel)
    }
    # If len params equals len `Depends` params, no other params accepted.
    accepts_caller_details = len(signature.parameters) != len(depends_params)
    return DependsModel(
        function=function,
        depends_params=depends_params,
        accepts_caller_details=accepts_caller_details,
    )


Depends = _depends
