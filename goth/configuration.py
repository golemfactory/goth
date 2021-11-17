"""Defines a class representing `goth` configuration."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import dpath.util
import yaml

from goth.address import YAGNA_REST_URL, PROXY_HOST
from goth.runner.container.compose import (
    ComposeConfig,
    DEFAULT_COMPOSE_FILE,
    YagnaBuildEnvironment,
)
from goth.runner.container.payment import PaymentIdPool
from goth.node import node_environment
from goth.runner.probe import Probe, YagnaContainerConfig
from goth.payment_config import get_payment_config, PaymentConfig

DEFAULT_PAYMENT_CONFIG_NAME = "erc20"
"""Determines PaymentConfig object that will be used for containers
without specified "payment-config" """

Override = Tuple[str, Any]
"""Type representing a single value override in a YAML config file.

First element is a path within the file, e.g.: `"docker-compose.build-environment"`.
Second element is the value to be inserted under the given path.
"""


class Configuration:
    """Configuration of a `goth` test network."""

    containers: List[YagnaContainerConfig]
    """A list of container configurations for nodes in the test network."""

    web_root: Optional[Path]
    """Path to the root directory of the built-in web server.

    `None` means that the web server will not be started.
    """

    compose_config: ComposeConfig
    """Configuration of the underlying docker compose network.

    Contains also the build environment description for yagna containers.
    """

    def __init__(
        self,
        compose_config: ComposeConfig,
        payment_id_pool: PaymentIdPool,
        web_root: Optional[Path] = None,
    ):
        self.containers: List[YagnaContainerConfig] = []
        self.compose_config = compose_config
        self._id_pool: PaymentIdPool = payment_id_pool
        self.web_root = web_root

    def add_node(
        self,
        type: Type[Probe],
        name: str,
        use_proxy: bool,
        privileged_mode: bool,
        payment_config: PaymentConfig,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[Path, Path]] = None,
        **kwargs,
    ) -> None:
        """Add configuration of a new requestor or provider node."""

        if use_proxy:
            node_env = node_environment(
                rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
                payment_env=payment_config.env,
            )
        else:
            node_env = node_environment(payment_env=payment_config.env)
        if environment:
            node_env.update(environment)

        container_cfg = YagnaContainerConfig(
            name=name,
            probe_type=type,
            payment_config=payment_config,
            environment=node_env,
            privileged_mode=privileged_mode,
            subnet="goth",
            volumes=volumes,
            payment_id=self._id_pool.get_id(payment_config),
            use_proxy=use_proxy,
            **kwargs,
        )

        self.containers.append(container_cfg)


class ConfigurationParseError(Exception):
    """An exception raised when parsing a malformed configuration file."""


class _ConfigurationParser:
    """A class for reading `goth` configuration from a `dict` instance."""

    Doc = Union[Dict[str, Any], List[Any]]
    """Type for documents parsed by _ConfigurationParser."""

    def __init__(self, doc: Doc, config_path: Optional[Path], root_key: str = ""):
        self._doc: _ConfigurationParser.Doc = doc
        self._config_path: Optional[Path] = config_path
        self.key: str = root_key

    def __contains__(self, key: Union[int, str]) -> bool:
        return key in self._doc

    def __getitem__(self, key: Union[int, str]) -> Any:
        child_key = self.key + (f".{key}" if isinstance(key, str) else f"[{key}]")
        try:
            value = self._doc[key]
            return (
                _ConfigurationParser(value, self._config_path, child_key)
                if isinstance(value, (dict, list))
                else value
            )
        except KeyError:
            raise ConfigurationParseError(f"Required key is missing: {child_key}")

    def __iter__(self):
        if isinstance(self._doc, dict):
            return iter(self._doc)

        assert isinstance(self._doc, list)
        for index in range(len(self._doc)):
            yield self[index]

    def ensure_type(self, expected: Type) -> None:
        if not isinstance(self._doc, expected):
            raise ConfigurationParseError(
                f"Expected a {expected.__name__} at {self.key}, "
                f"found a {type(self.doc).__name__}"
            )

    @property
    def doc(self) -> Doc:
        """Return the underlying dictionary or list."""
        return self._doc

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value assigned to `key` if defined, otherwise return `default`."""
        return self[key] if key in self else default

    def resolve_path(self, path_str: str) -> Path:
        """Return `path` resolved relative to the directory of the config file."""
        path = Path(path_str).expanduser()
        return (self._config_path.parent / path).resolve()

    def get_path(self, key: str, required: bool = True) -> Optional[Path]:
        """Return a path assigned to `key`, resolved with `self.resolve_path()`."""
        path_opt = self[key] if required else self.get(key)
        return self.resolve_path(path_opt) if path_opt else None

    def read_volumes_spec(self) -> Dict[Path, str]:
        """Read a specification of volumes from this parser's document."""
        self.ensure_type(list)
        volumes = {}
        for mount_spec in self:
            dest = mount_spec["destination"]
            # TODO: "read-only"/"read-write" are the same; both will mount r/w
            # In future, "read-write" should probably copy the asset pointed to
            # by `source` to a temp file/dir, and mount that copied file/dir
            # in a read/write mode
            if "read-only" in mount_spec:
                source = mount_spec.get_path("read-only")
                volumes[source] = dest
            # TODO: "read-write" should
            elif "read-write" in mount_spec:
                source = mount_spec.get_path("read-write")
                volumes[source] = dest
        return volumes

    def read_environment(self) -> Dict[str, str]:
        """Read a specification of environment variables from this parser's document.

        The variables must be strings in the form: "{NAME}={VALUE}".
        """
        self.ensure_type(list)
        environment = {}
        for env_var in self:
            name_value_pair = env_var.split("=", 1)
            if len(name_value_pair) != 2:
                raise ConfigurationParseError(
                    f"Invalid format of environment variable {env_var}, "
                    f"expected `VAR_NAME=VAR_VALUE`."
                )
            name, value = name_value_pair
            environment[name] = value
        return environment

    def read_compose_config(self) -> ComposeConfig:
        """Read a `ComposeConfig` instance from this parser's document."""
        self.ensure_type(dict)

        docker_dir = self.get_path("docker-dir")
        assert docker_dir

        log_patterns = self.get("compose-log-patterns")
        log_patterns.ensure_type(dict)

        compose_file = self.get("compose-file", DEFAULT_COMPOSE_FILE)
        build_env_config = self.get("build-environment")
        # `build_env_config` may be `None` if no optional build parameters
        # (binary path, commit hash etc.) are specified in the config file
        if build_env_config:
            build_env_config.ensure_type(dict)
            build_env = build_env_config.read_build_env(docker_dir)
        else:
            build_env = YagnaBuildEnvironment(docker_dir)

        return ComposeConfig(build_env, docker_dir / compose_file, log_patterns.doc)

    def read_build_env(self, docker_dir: Path) -> YagnaBuildEnvironment:
        """Read a `YagnaBuildEnvironment` instance from this parser's document."""
        self.ensure_type(dict)

        binary_path = self.get_path("binary-path", required=False)
        branch = self.get("branch")
        commit_hash = self.get("commit-hash")
        deb_path = self.get_path("deb-path", required=False)
        release_tag = self.get("release-tag")
        use_prerelease = self.get("use-prerelease", default=True)
        return YagnaBuildEnvironment(
            docker_dir,
            binary_path=binary_path,
            branch=branch,
            commit_hash=commit_hash,
            deb_path=deb_path,
            release_tag=release_tag,
            use_prerelease=use_prerelease,
        )


def load_yaml(
    yaml_path: Union[Path, str], overrides: Optional[List[Override]] = None
) -> Configuration:
    """Load a configuration from a YAML file at `yaml_path'.

    It's possible to override values from the YAML file through the use of `overrides`.
    Each override is a tuple of a dict path and a value to insert at that path.
    Dict paths are dot-separated flattened paths in the YAML file, e.g.:
    `"docker-compose.build-environment.binary-path"`.

    Currently, it's not possible to override values inside a list as there's no support
    for indexing lists in the config file.
    """

    import importlib

    with open(str(yaml_path)) as f:
        dict_: Dict[str, Any] = yaml.load(f, yaml.FullLoader)
        if overrides:
            _apply_overrides(dict_, overrides)

        network = _ConfigurationParser(dict_, Path(yaml_path))

        key_dir = network.get_path("key-dir")
        compose_config = network["docker-compose"].read_compose_config()
        web_root = network.get_path("web-root", required=False)

        config = Configuration(compose_config, PaymentIdPool(key_dir=key_dir), web_root)

        node_types = {}
        for node_type in network["node-types"]:
            name = node_type["name"]
            type_name = node_type["class"]
            try:
                mod_name, class_name = type_name.rsplit(".", 1)
                module = importlib.import_module(mod_name)
                class_ = module.__dict__[class_name]
                assert isinstance(class_, type)
                assert issubclass(class_, Probe)
            except (AssertionError, KeyError, ValueError):
                raise ConfigurationParseError(
                    f"The value '{type_name}' of {node_type.key + '.class'} "
                    f"does not refer to a subclass of {Probe.__name__}"
                )
            mounts = node_type.get("mount")
            volumes = mounts.read_volumes_spec() if mounts else {}

            env = node_type.get("environment")
            env_dict = env.read_environment() if env else {}

            privileged_mode = node_type.get("privileged-mode", False)

            node_types[name] = (class_, volumes, privileged_mode, env_dict)

        for node in network["nodes"]:
            name = node["name"]
            type_name = node["type"]
            use_proxy = node.get("use-proxy", False)

            payment_config_name = node.get(
                "payment-config", DEFAULT_PAYMENT_CONFIG_NAME
            )
            payment_config = get_payment_config(payment_config_name)

            class_, volumes, privileged_mode, env_dict = node_types[type_name]
            config.add_node(
                class_,
                name,
                use_proxy=use_proxy,
                privileged_mode=privileged_mode,
                environment=env_dict,
                volumes=volumes,
                payment_config=payment_config,
            )

    return config


def _apply_overrides(dict_: Dict[str, Any], overrides: List[Override]):
    for (dict_path, value) in overrides:
        path_list: List[str] = dict_path.split(".")

        leaf = dpath.util.get(dict_, path_list, default=None)
        # if the path's last element does not exist, add it as a new dict
        if not leaf:
            leaf_name = path_list.pop()
            value = {leaf_name: value}

        dpath.util.new(dict_, path_list, value)
