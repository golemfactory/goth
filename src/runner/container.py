from enum import Enum
from typing import DefaultDict, Dict

from docker.models.containers import Container
import docker


class YagnaContainer:
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    ENVIRONMENT = [
        "YAGNA_BUS_PORT=6010",
        "YAGNA_HTTP_PORT=6000",
        "CENTRAL_NET_HOST=router:7477",
        "GSB_URL=tcp://0.0.0.0:6010",
        "YAGNA_MARKET_URL=http://mock-api:5001/market-api/v1/",
        "YAGNA_API_URL=http://0.0.0.0:6000",
        "YAGNA_ACTIVITY_URL=http://127.0.0.1:6000/activity-api/v1/",
    ]
    IMAGE_NAME = "yagna"
    NETWORK_NAME = "docker_default"

    # Keeps track of assigned ports on the Docker host
    port_offset = 0

    def __init__(
        self,
        client: docker.DockerClient,
        name: str,
        volumes: Dict[str, str],
        ordinal: int = 1,
    ):
        self.client = client

        self.ports = {
            YagnaContainer.HTTP_PORT: YagnaContainer.host_http_port(),
            YagnaContainer.BUS_PORT: YagnaContainer.host_bus_port(),
        }

        self.volumes: Dict[str, dict] = {}
        for host_path, cont_path in volumes.items():
            self.volumes[host_path] = {"bind": cont_path, "mode": "ro"}

        self.name = f"yagna_{name}_{ordinal}"
        YagnaContainer.port_offset += 1

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls.port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls.port_offset

    def run(self, auto_remove: bool = True) -> Container:
        return self.client.containers.run(
            self.IMAGE_NAME,
            entrypoint=self.ENTRYPOINT,
            command=self.COMMAND,
            detach=True,
            environment=self.ENVIRONMENT,
            name=self.name,
            network=self.NETWORK_NAME,
            ports=self.ports,
            volumes=self.volumes,
            auto_remove=auto_remove,
        )
