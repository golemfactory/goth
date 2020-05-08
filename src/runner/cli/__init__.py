"""Classes for running commands inside docker containers"""

from docker.models.containers import Container, ExecResult

from .base import DockerJSONCommandRunner
from .yagna_app_key_cmd import YagnaAppKeyMixin
from .yagna_id_cmd import YagnaIdMixin
from .yagna_payment_cmd import YagnaPaymentMixin


class YagnaDockerCli(
    DockerJSONCommandRunner, YagnaAppKeyMixin, YagnaIdMixin, YagnaPaymentMixin
):
    """A class for running the `yagna` command inside a docker container"""

    def __init__(self, container: Container):
        super().__init__(container, "yagna")


class Cli:
    """A class for running multiple commands inside a docker container"""

    yagna: YagnaDockerCli
    """A command-line interface for the `yagna` command"""

    def __init__(self, container: Container):
        self.yagna = YagnaDockerCli(container)
