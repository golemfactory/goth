from enum import Enum
import logging
from pathlib import Path
from typing import Optional

from docker import DockerClient

from goth.runner.cli import Cli
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from goth.runner.exceptions import KeyAlreadyExistsError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor


logger = logging.getLogger(__name__)


class Role(Enum):
    requestor = 0
    provider = 1


class Probe:
    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        self.container = YagnaContainer(client, config, log_config, assets_path)
        self.cli = Cli(self.container).yagna
        self.role = config.role

        self.agent_logs: LogEventMonitor

    def __str__(self):
        return self.name

    async def stop(self):
        self.container.remove(force=True)
        if self.container.log_config:
            await self.container.logs.stop()

        if self.agent_logs:
            await self.agent_logs.stop()

    @property
    def address(self) -> Optional[str]:
        """ returns address from id marked as default """
        identity = self.cli.id_show()
        return identity.address if identity else None

    @property
    def app_key(self) -> Optional[str]:
        """ returns first app key on the list """
        keys = self.cli.app_key_list()
        return keys[0].key if keys else None

    @property
    def name(self) -> str:
        return self.container.name

    def create_app_key(self, key_name: str) -> str:
        try:
            key = self.cli.app_key_create(key_name)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    def init_payments(self, probe):
        print("init_payments()")
        print(probe)
        print(probe == Role.requestor)
        self.cli.payment_init(
            requestor_mode=probe == Role.requestor,
            provider_mode=probe == Role.provider,
        )

    def start_provider_agent(self, preset_name: str):
        log_stream = self.container.exec_run(
            f"ya-provider run"
            f" --app-key {self.app_key} --node-name {self.name} {preset_name}",
            stream=True,
        )
        self._init_agent_logs(log_stream)

    def start_requestor_agent(self):
        log_stream = self.container.exec_run(
            f"ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json",
            stream=True,
        )
        self._init_agent_logs(log_stream)

    def _init_agent_logs(self, log_stream):
        log_config = LogConfig(
            file_name=f"{self.name}_agent", base_dir=self.container.log_config.base_dir,
        )
        self.agent_logs = LogEventMonitor(log_stream.output, log_config)
