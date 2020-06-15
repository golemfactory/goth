from pathlib import Path
from string import Template
from typing import Dict, Optional

from docker import DockerClient

from src.runner.container import DockerContainer, DockerContainerConfig
from src.runner.log import LogConfig


class ProxyContainerConfig(DockerContainerConfig):
    """Configuration for a proxy container"""

    stop_on_error: bool = True
    """Should the proxy stop as soon as an assertion fails"""

    def __init__(
        self,
        name: str,
        volumes: Optional[Dict[Template, str]] = None,
        log_config: Optional[LogConfig] = None,
        stop_on_error: bool = True,
    ):
        super().__init__(name, volumes or {}, log_config)
        self.stop_on_error = stop_on_error


class ProxyContainer(DockerContainer):
    """A `DockerContainer` subclass for running mitmproxy nodes as part of test setup"""

    IMAGE = "api-monitor"
    ENTRYPOINT = "./start-proxy.sh"

    def __init__(
        self,
        client: DockerClient,
        config: ProxyContainerConfig,
        log_config: Optional[LogConfig] = None,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        super().__init__(
            client,
            command=[],
            entrypoint=self.ENTRYPOINT,
            image=self.IMAGE,
            log_config=log_config,
            name=config.name,
            environment={},
            ports={},
            volumes=config.get_volumes_spec(assets_path) if assets_path else {},
            hostname=config.name,
            **kwargs,
        )
