"""Built-in web server for serving test assets such as task packages."""

import asyncio
import contextlib
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web, web_runner


logger = logging.getLogger(__name__)

DEFAULT_SERVER_PORT = 9292


class WebServer:
    """A simple web server implemented with the `aiohttp` library."""

    _server_task: Optional[asyncio.Task] = None
    """An asyncio task wrapping the `aiohttp` server coroutine.

    Not None iff the server is running."""

    root_path: Path
    """A directory from which the content is served."""

    server_port: int
    """A port on which the server listens."""

    def __init__(self, root_path: Path, server_port: int):
        self.root_path = root_path
        self.server_port = server_port

    async def _upload_handler(self, request: web.Request) -> web.Response:
        logger.debug("Handling upload request...")
        upload_path = self.root_path / "upload" / request.match_info["filename"]
        with open(upload_path, "wb") as out:
            async for data in request.content.iter_any():
                out.write(data)
        return web.Response()

    @contextlib.asynccontextmanager
    async def run(self, server_address: Optional[str]) -> None:
        """Implement AsyncContextManager protocol for a web server."""

        try:
            await self.start(server_address)
            yield
        finally:
            await self.stop()

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
        site = web.TCPSite(runner, server_address, self.server_port)
        self._server_task = asyncio.create_task(site.start())
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
        self._server_task.cancel()
        await self._server_task
        self._server_task = None
        logger.info("Stopped the web server")
