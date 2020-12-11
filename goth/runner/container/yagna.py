"""Classes to help configure and create `YagnaContainer`s."""

from pathlib import Path
from typing import Any, ClassVar, Dict, Iterator, Optional, Type, TYPE_CHECKING

from docker import DockerClient
from goth.address import (
    HOST_REST_PORT_END,
    HOST_REST_PORT_START,
    YAGNA_REST_PORT,
)
from goth.runner.container import DockerContainer, DockerContainerConfig
import goth.runner.container.payment as payment
import goth.runner.container.utils as utils
from goth.runner.log import LogConfig

if TYPE_CHECKING:
    from goth.runner.probe import Probe  # noqa: F401

# Default path for mounting assets within a yagna container
ASSET_MOUNT_PATH = Path("/asset")
# Path for mounting payment IDs inside a yagna container
PAYMENT_MOUNT_PATH = ASSET_MOUNT_PATH / "payment"


class YagnaContainerConfig(DockerContainerConfig):
    """Configuration to be used for creating a new `YagnaContainer`."""

    probe_type: Type["Probe"]
    """Python type of the probe to be instantiated from this config."""

    probe_properties: Dict[str, Any]
    """Additional properties to be set on the probe object."""

    environment: Dict[str, str]
    """Environment variables to be set for this container."""

    payment_id: Optional[payment.PaymentId]
    """Custom key and payment accounts to be imported into yagna ID service."""

    def __init__(
        self,
        name: str,
        probe_type: Type["Probe"],
        volumes: Optional[Dict[Path, str]] = None,
        log_config: Optional[LogConfig] = None,
        environment: Optional[Dict[str, str]] = None,
        privileged_mode: bool = False,
        payment_id: Optional[payment.PaymentId] = None,
        **probe_properties,
    ):
        super().__init__(name, volumes or {}, log_config, privileged_mode)
        self.probe_type = probe_type
        self.probe_properties = probe_properties or {}
        self.environment = environment or {}
        self.payment_id = payment_id


class YagnaContainer(DockerContainer):
    """Extension of DockerContainer to be configured for yagna daemons."""

    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna-goth"

    ports: Dict[int, int] = {}
    """ Port mapping between the Docker host and the container.
        Keys are container port numbers, values are host port numbers. """

    host_port_range: ClassVar[Iterator[int]] = iter(
        range(HOST_REST_PORT_START, HOST_REST_PORT_END)
    )
    """ Keeps track of assigned ports on the Docker host """

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: Optional[LogConfig] = None,
        **kwargs,
    ):
        self.ports = {YAGNA_REST_PORT: YagnaContainer.host_rest_port()}

        super().__init__(
            client=client,
            command=self.COMMAND,
            entrypoint=self.ENTRYPOINT,
            environment=self._prepare_environment(config),
            image=self.IMAGE,
            log_config=log_config,
            name=config.name,
            ports=self.ports,
            volumes=self._prepare_volumes(config),
            privileged=config.privileged_mode,
            **kwargs,
        )

    @classmethod
    def host_rest_port(cls):
        """Return the next host port that can be used for port mapping.

        Raises `OverflowError` if the port to return would exceed the expected range.
        """
        try:
            return next(cls.host_port_range)
        except StopIteration:
            raise OverflowError(f"Port range exceeded. range_end={HOST_REST_PORT_END}")

    def _prepare_volumes(self, config: YagnaContainerConfig) -> Dict[str, dict]:
        volumes_spec = utils.get_volumes_spec(config.volumes)
        if config.payment_id:
            id_volumes = {payment.get_id_directory(): str(PAYMENT_MOUNT_PATH)}
            id_volumes_spec = utils.get_volumes_spec(id_volumes, writable=False)
            volumes_spec.update(id_volumes_spec)
        return volumes_spec

    def _prepare_environment(self, config: YagnaContainerConfig) -> Dict[str, str]:
        env = config.environment
        if config.payment_id:
            accounts_file_name = config.payment_id.accounts_file.name
            mount_path = str(PAYMENT_MOUNT_PATH / accounts_file_name)
            env[payment.ENV_ACCOUNT_LIST] = mount_path
        return env
