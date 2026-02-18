"""Example dependency injection."""

from collections.abc import Awaitable
from sqlite3 import Connection, connect
from typing import Annotated, Callable

from aiohttp import web
from jsonrpcobjects.objects import ErrorResponse
from openrpc import BaseContext, Inject, RPCApp, parse_request

rpc = RPCApp()


class Context(BaseContext):
    def __init__(self, conn: Connection, scopes: list[str] | None = None) -> None:
        self.conn = conn
        super().__init__(scopes)


def _connect(context: Context) -> Connection:
    return context.conn


InjectConnection = Annotated[Connection, Inject(_connect)]


@rpc.method()
def add_string(string: str, conn: InjectConnection) -> None:
    cursor = conn.cursor()
    _ = cursor.execute('insert into "strings" values (?)', (string,))


def get_api_method() -> Callable[[web.Request], Awaitable[web.Response]]:
    conn = connect(":memory:")
    _ = conn.cursor().execute('create table "strings" ("value" TEXT)')
    conn.commit()

    async def api(request: web.Request) -> web.Response:
        raw_request = await request.text()
        parsed = parse_request(raw_request)
        context = Context(conn)
        if isinstance(parsed, list):
            raise NotImplementedError()
        result = await rpc.process_parsed_request(parsed, context)
        if result is not None:
            response_content = result.model_dump_json(by_alias=True)
        else:
            response_content = None
        if isinstance(result, ErrorResponse):
            conn.rollback()
        else:
            conn.commit()
        return web.Response(body=response_content)

    return api


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", get_api_method())
    web.run_app(app)
