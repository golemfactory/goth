"""Exceptions raised by the runner."""


class CommandError(Exception):
    """Error while running a command on a DockerMachine."""

    def __init__(self, message: str):
        super().__init__(message)


class KeyAlreadyExistsError(CommandError):
    """Specific duplucate key subclass of the CommandError."""

    pass


class ContainerNotFoundError(Exception):
    """Exception for when the container is not found."""

    pass


class TimeoutError(Exception):
    """Exception for when a timeout occurs."""

    pass
