"""Minimal `aiohttp` RPC demo."""

from aiohttp import web
from openrpc import RPCApp

rpc = RPCApp()


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


async def api(request: web.Request) -> web.Response:
    return web.Response(body=await rpc.process(await request.text()))


if __name__ == "__main__":
    app = web.Application()
    _ = app.router.add_post("/api", api)
    web.run_app(app)
