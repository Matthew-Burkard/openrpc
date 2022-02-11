"""Shared utilities across the project."""
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Function:
    """Hold information about a decorated Python function."""

    function: Callable
    metadata: dict[str, Any]
