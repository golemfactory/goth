from enum import Enum
import logging
from typing import Optional

from docker.models.containers import Container

from src.runner.cli import Cli
from src.runner.exceptions import KeyAlreadyExistsError
from src.runner.log import get_file_logger, LogBuffer


logger = logging.getLogger(__name__)


class Role(Enum):
    requestor = 0
    provider = 1


class Probe:
    def __init__(self, container: Container, role: Role):
        self.container = container
        self.cli = Cli(container).yagna
        self.logs = LogBuffer(
            container.logs(stream=True, follow=True), get_file_logger(self.name)
        )
        self.role = role

        self.agent_logs: LogBuffer

    def __str__(self):
        return self.name

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

    def start_provider_agent(self, preset_name: str):
        log_stream = self.container.exec_run(
            f"ya-provider run --app-key {self.app_key} --node-name {self.name} {preset_name}",
            stream=True,
        )
        self.agent_logs = LogBuffer(
            log_stream.output, get_file_logger(f"{self.name}_agent")
        )

    def start_requestor_agent(self):
        log_stream = self.container.exec_run(
            f"ya-requestor --app-key {self.app_key} --exe-script /asset/exe_script.json",
            stream=True,
        )
        self.agent_logs = LogBuffer(
            log_stream.output, get_file_logger(f"{self.name}_agent")
        )
