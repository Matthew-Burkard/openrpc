import uuid
from typing import Union

from openrpc.rpc_client import RPCDirectClient
from rpc_objects import ErrorResponseObject, RequestObjectParams


class MathRPCClient(RPCDirectClient):

    def add(self, x: float, y: float) -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(str(uuid.uuid4()), 'add', [x, y])
        )

    def subtract(
            self,
            x: float,
            y: float
    ) -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(str(uuid.uuid4()), 'subtract', [x, y])
        )

    def divide(self, x: float, y: float) -> Union[float, ErrorResponseObject]:
        return self._call(
            RequestObjectParams(str(uuid.uuid4()), 'divide', [x, y])
        )
