"""Minimal `aiohttp` RPC demo."""

from aiohttp import web
from openrpc import BaseContext, RPCApp, Scope

rpc = RPCApp()

add_numbers = Scope(name="numbers:add", description="Permission to add two numbers.")


@rpc.method(scopes=[add_numbers])
async def add(a: int, b: int) -> int:
    return a + b


def _get_scopes_from_token(token: str) -> list[str]: ...


async def api(request: web.Request) -> web.Response:
    context = BaseContext(
        scopes=_get_scopes_from_token(request.headers["Authorization"])
    )
    return web.Response(body=await rpc.process(await request.text(), context))


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", api)
    web.run_app(app)
