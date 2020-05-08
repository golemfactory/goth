from collections import defaultdict
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

    # Keeps track of ordinals for containers with the same names, e.g. multiple providers
    ordinals: DefaultDict[str, int] = defaultdict(int)

    def __init__(self, client: docker.DockerClient, name: str, volumes: Dict[str, str]):
        self.client = client

        port_offset = YagnaContainer.ordinals[name] + sum(
            YagnaContainer.ordinals.values()
        )
        self.ports = {
            YagnaContainer.HTTP_PORT: YagnaContainer.HTTP_PORT + port_offset,
            YagnaContainer.BUS_PORT: YagnaContainer.BUS_PORT + port_offset,
        }

        self.volumes: Dict[str, dict] = {}
        for host_path, cont_path in volumes.items():
            self.volumes[host_path] = {"bind": cont_path, "mode": "ro"}

        YagnaContainer.ordinals[name] += 1
        self.name = f"yagna_{name}_{YagnaContainer.ordinals[name]}"

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
            remove=True,
        )
