"""Built-in web server for serving test assets such as task packages."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web, web_runner


logger = logging.getLogger(__name__)


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

    async def start(self, server_address: Optional[str]) -> None:
        """Start serving content."""

        if self._server_task:
            logger.warning("Tried to start a web server that is already running")
            return

        app = web.Application()
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

        self._server_task.cancel()
        await self._server_task
        self._server_task = None
        logger.info("Stopped the web server")
