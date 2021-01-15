"""Exceptions raised by the runner."""


class CommandError(Exception):
    """Error while running a command on a DockerMachine."""

    def __init__(self, message: str):
        super().__init__(message)


class ContainerNotFoundError(Exception):
    """Exception for when the container is not found."""

    def __init__(self, name: str):
        super().__init__(f"No container with name containing '{name}' was found.")


class KeyAlreadyExistsError(CommandError):
    """Specific duplicate key subclass of the CommandError."""


class StopThreadException(Exception):
    """Exception used to stop a running `StoppableThread`."""


class TimeoutError(Exception):
    """Exception for when a timeout occurs."""
