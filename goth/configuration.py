"""Defines a class representing `goth` configuration."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import yaml

from goth.address import YAGNA_REST_URL, PROXY_HOST
from goth.runner.container.payment import PaymentIdPool
from goth.node import node_environment
from goth.runner.probe import Probe, RequestorProbe, YagnaContainerConfig
from goth.runner.provider import ProviderProbeWithLogSteps


class Configuration:
    """Configuration of a `goth` test network."""

    containers: List[YagnaContainerConfig]
    """A list of container configurations for nodes in the test network."""
    docker_dir: Path
    """Path to the directory with docker compose and docker files."""
    web_root: Path
    """Path to the root directory of the built-in web server."""
    # TODO: Allow `None`, meaning: don't start the web server

    def __init__(
        self, payment_id_pool: PaymentIdPool, docker_dir: Path, web_root: Path
    ):
        self.containers: List[YagnaContainerConfig] = []
        self.docker_dir = docker_dir
        self._id_pool: PaymentIdPool = payment_id_pool
        self.web_root = web_root

    @property
    def compose_file(self) -> Path:
        """Return the path to `docker-compose.yml` used in this configuration."""
        return self.docker_dir / "docker-compose.yml"

    def _add_node(
        self,
        type: Type[Probe],
        name: str,
        use_proxy: bool,
        privileged_mode: bool,
        volumes: Optional[Dict[Path, Path]],
        **kwargs,
    ) -> None:
        """Add configuration of a new requestor or provider node."""

        if use_proxy:
            node_env = node_environment(
                rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST)
            )
        else:
            node_env = node_environment()

        container_cfg = YagnaContainerConfig(
            name=name,
            probe_type=type,
            environment=node_env,
            privileged_mode=privileged_mode,
            subnet="goth",
            volumes=volumes,
            **kwargs,
        )

        self.containers.append(container_cfg)

    def add_provider_node(
        self,
        name: str,
        use_proxy: bool = True,
        privileged_mode: bool = False,
        volumes: Optional[Dict[Path, Path]] = None,
    ) -> None:
        """Add a provider node configuration to the test network."""

        # TODO: should we make requestor/provider probe classes configurable?
        self._add_node(
            ProviderProbeWithLogSteps, name, use_proxy, privileged_mode, volumes
        )

    def add_requestor_node(
        self,
        name: str,
        use_proxy: bool = False,
        volumes: Optional[Dict[Path, str]] = None,
    ) -> None:
        """Add a requestor node configuration to the test network."""

        # TODO: should we make requestor/provider probe classes configurable?
        self._add_node(
            RequestorProbe,
            name,
            use_proxy,
            False,
            volumes,
            payment_id=self._id_pool.get_id(),
        )


class _ConfigurationParser:
    """A class for reading `goth` configuration from a `dict` instance."""

    def __init__(
        self,
        doc: Union[Dict[str, Any], List[Any]],
        config_path: Optional[Path],
        root_key: Optional[List[str]],
    ):
        self._doc: Union[Dict[str, Any], List[Any]] = doc
        self._config_path: Optional[Path] = config_path
        self._root_key: List[str] = root_key

    def __contains__(self, key: Union[int, str]) -> bool:
        return key in self._doc

    def __getitem__(self, key: Union[int, str]) -> Any:
        try:
            value = self._doc[key]
            return (
                _ConfigurationParser(
                    value, self._config_path, self._root_key + [str(key)]
                )
                if isinstance(value, (dict, list))
                else value
            )
        except KeyError:
            keys = self._root_key + [str(key)]
            return KeyError(".".join(keys))

    def __iter__(self):

        if isinstance(self._doc, dict):
            return iter(self._doc)

        assert isinstance(self._doc, list)
        for index in range(len(self._doc)):
            yield self[index]

    @property
    def doc(self) -> Union[Dict[str, Any], List[Any]]:
        """Return the underlying dictionary or list."""
        return self._doc

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value assigned to `key` if defined, otherwise return `default`."""
        return self[key] if key in self else default

    def resolve_path(self, path: str) -> Path:
        """Return `path` resolved relative to the directory of the config file."""
        return (self._config_path.parent / Path(path)).resolve()

    def get_path(self, key: str, required: bool = True) -> Optional[Path]:
        """Return a path assigned to `key`, resolved with `self.resolve_path()`."""
        path_opt = self[key] if required else self.get(key)
        return self.resolve_path(path_opt) if path_opt else None

    def read_volumes_spec(self) -> Dict[Path, str]:
        if not isinstance(self._doc, list):
            raise TypeError(
                f"Volume specification may be read from a list, not a {type(self._doc)}"
            )
        volumes = {}
        for mount_spec in self:
            dest = mount_spec["destination"]
            # TODO: "read-only"/"read-write" are the same; both will mount r/w
            # In future, "read-write" should probably copy the asset pointed to
            # by `source` to a temp file/dir, and mount that copied file/dir
            # in a read/write mode
            if "read-only" in mount_spec:
                source = self.resolve_path(mount_spec["read-only"])
                volumes[source] = dest
            # TODO: "read-write" should
            elif "read-write" in mount_spec:
                source = self.resolve_path(mount_spec["read-write"])
                volumes[source] = dest
        return volumes


def load_yaml(yaml_path: Path) -> Configuration:
    """Load a configuration from a YAML file at `yaml_path'."""

    with open(str(yaml_path)) as f:
        dict_ = yaml.load(f)
        network = _ConfigurationParser(dict_, yaml_path, [])

        key_dir = network.get_path("key-dir")
        docker_dir = network.get_path("docker-dir")
        web_root = network.get_path("web-root", required=False)

        config = Configuration(PaymentIdPool(key_dir=key_dir), docker_dir, web_root)

        requestor = network["requestor"]
        use_proxy = requestor.get("use-proxy", False)
        mounts = requestor.get("mount")
        volumes = mounts.read_volumes_spec() if mounts else {}

        config.add_requestor_node(requestor["name"], use_proxy, volumes)

        for provider_type in network["providers"]:
            names = (
                [provider_type["name"]]
                if "name" in provider_type
                else provider_type["names"]
            )
            mounts = provider_type.get("mount")
            volumes = mounts.read_volumes_spec() if mounts else {}
            use_proxy = provider_type.get("use-proxy", False)

            for name in names:
                config.add_provider_node(name, use_proxy, True, volumes)

        return config
