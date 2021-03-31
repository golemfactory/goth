"""Built-in web server for serving test assets such as task packages."""

import asyncio
import contextlib
from itertools import cycle
import logging
from pathlib import Path
from typing import Iterator, Optional

from aiohttp import web, web_runner

from goth.address import WEB_SERVER_PORT_END, WEB_SERVER_PORT_START


logger = logging.getLogger(__name__)


class WebServer:
    """A simple web server implemented with the `aiohttp` library."""

    root_path: Path
    """A directory from which the content is served."""

    server_port: int
    """A port on which the server listens."""

    _port_pool: Iterator[int] = cycle(range(WEB_SERVER_PORT_START, WEB_SERVER_PORT_END))
    """Iterator which cycles indefinitely through the range of assigned ports."""

    _server_task: Optional[asyncio.Task] = None
    """An asyncio task wrapping the `aiohttp` server coroutine.

    Not None iff the server is running."""

    _site: web.TCPSite
    """Site object for the TCP socket of this server."""

    def __init__(self, root_path: Path, server_port: Optional[int] = None):
        self.root_path = root_path
        self.server_port = server_port or next(self._port_pool)

    async def _upload_handler(self, request: web.Request) -> web.Response:
        logger.debug("Handling upload request...")
        upload_path = self.root_path / "upload" / request.match_info["filename"]
        with open(upload_path, "wb") as out:
            async for data in request.content.iter_any():
                out.write(data)
        return web.Response()

    async def start(self, server_address: Optional[str]) -> None:
        """Start serving content."""

        if self._server_task:
            logger.warning("Tried to start a web server that is already running")
            return

        app = web.Application()
        app.router.add_put("/upload/{filename}", self._upload_handler)
        app.router.add_static("/", path=Path(self.root_path), name="root")
        runner = web_runner.AppRunner(app)
        await runner.setup()
        self._site = web.TCPSite(runner, server_address, self.server_port)
        self._server_task = asyncio.create_task(self._site.start())
        logger.info(
            "Web server listening on %s:%s, root dir is %s",
            server_address or "*",
            self.server_port,
            self.root_path,
        )

    async def stop(self) -> None:
        """Stop the server."""

        if not self._server_task:
            logger.warning("Tried to stop a web server that is not running")
            return

        if self._server_task.done() and self._server_task.exception():
            await self._server_task

        await self._site.stop()
        self._server_task.cancel()
        await self._server_task
        self._server_task = None
        logger.info("Stopped the web server")


@contextlib.asynccontextmanager
async def run_web_server(server: WebServer, server_address: Optional[str]) -> None:
    """Implement AsyncContextManager protocol for starting/stopping a web server."""

    try:
        logger.debug("Starting web server. address=%s", server_address)
        await server.start(server_address)
        yield
    finally:
        logger.debug("Stopping web server. address=%s", server_address)
        await server.stop()
