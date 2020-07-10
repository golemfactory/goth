"""Classes for running commands inside docker containers."""

from goth.runner.cli.base import DockerJSONCommandRunner
from goth.runner.cli.yagna_app_key_cmd import YagnaAppKeyMixin
from goth.runner.cli.yagna_id_cmd import YagnaIdMixin
from goth.runner.cli.yagna_payment_cmd import YagnaPaymentMixin
from goth.runner.container import DockerContainer


class YagnaDockerCli(
    DockerJSONCommandRunner, YagnaAppKeyMixin, YagnaIdMixin, YagnaPaymentMixin
):
    """A class for running the `yagna` command inside a docker container."""

    def __init__(self, container: DockerContainer):
        super().__init__(container, "yagna")


class Cli:
    """A class for running multiple commands inside a docker container."""

    yagna: YagnaDockerCli
    """A command-line interface for the `yagna` command."""

    def __init__(self, container: DockerContainer):
        self.yagna = YagnaDockerCli(container)
