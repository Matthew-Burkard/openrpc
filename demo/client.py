import uuid
from typing import Union

from openrpc.rpc_client import RPCDirectClient
from rpc_objects import ErrorResponseObject, RequestObjectParams


class MathRPCClient(RPCDirectClient):

    def discover(self) -> str:
        return self._call(
            RequestObjectParams(
                id=str(uuid.uuid4()),
                method='rpc.discover',
                params=[]
            )
        )

    def add(self, x: float, y: float) -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(
                id=str(uuid.uuid4()),
                method='add',
                params=[x, y]
            )
        )

    def subtract(self, x: float, y: float) \
            -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(
                id=str(uuid.uuid4()),
                method='subtract',
                params=[x, y]
            )
        )

    def divide(self, x: float, y: float) -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(
                id=str(uuid.uuid4()),
                method='divide',
                params=[x, y]
            )
        )
