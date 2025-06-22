"""Module providing RPC routers."""

from openrpc._method_registrar import MethodRegistrar


class RPCRouter(MethodRegistrar):
    """RPC method router."""

    def __init__(self) -> None:
        """Initialize a new instance of the RPCRouter class."""
        super().__init__()
