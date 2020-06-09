from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from docker import DockerClient

from src.runner.container import DockerContainer, DockerContainerConfig


@dataclass(frozen=True)
class ProxyContainerConfig(DockerContainerConfig):
    """Configuration for a proxy container"""

    stop_on_error: bool = True
    """Should the proxy stop as soon as an assertion fails"""


class ProxyContainer(DockerContainer):
    """A `DockerContainer` subclass for running mitmproxy nodes as part of test setup"""

    IMAGE = "api-monitor"
    ENTRYPOINT = "./start-proxy.sh"

    def __init__(
        self,
        client: DockerClient,
        config: ProxyContainerConfig,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        super().__init__(
            client,
            command=[],
            entrypoint=self.ENTRYPOINT,
            image=self.IMAGE,
            name=config.name,
            environment={},
            ports={},
            volumes=config.get_volumes_spec(assets_path) if assets_path else {},
            hostname=config.name,
            **kwargs,
        )
