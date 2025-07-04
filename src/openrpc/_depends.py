"""Module providing class to handle middleware dependencies."""

import inspect
from typing import Any, Callable, Union

from pydantic import BaseModel

from openrpc.context import Context


class DependsModel(BaseModel):
    """Supply with function used to return a dependent argument."""

    function: Callable[..., Any]
    depends_params: dict[str, "DependsModel"]
    accepts_caller_details: bool


def Depends(function: Callable[..., Any]) -> Any:  # noqa: N802
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


InjectFunction = Union[Callable[[], Any], Callable[[Context], Any]]


class InjectModel(BaseModel):
    """Supply with function used to return a dependent argument."""

    name: str = ""
    index: int = -1
    function: InjectFunction
    requires_context: bool


def Inject(function: Callable[..., Any]) -> Any:  # noqa: N802
    requires_context = len(inspect.signature(function).parameters) > 0
    return InjectModel(function=function, requires_context=requires_context)
