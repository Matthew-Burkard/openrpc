"""Module providing class to handle middleware dependencies."""
from typing import Any


class _Depends:
    """Used to identify a param as a dependency."""


Depends: Any = _Depends
