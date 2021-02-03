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


class TestFailure(Exception):
    """Base class for errors raised by the test runner when a test fails."""


class StepTimeoutError(TestFailure):
    """Raised on test step timeout."""

    def __init__(self, step: str, time: float):
        super().__init__(f"Step '{step}' timed out after {time:.1f} s")


class TemporalAssertionError(TestFailure):
    """Raised on temporal assertion failure."""

    def __init__(self, assertion: str):
        super().__init__(f"Temporal assertion '{assertion}' failed")


class TimeoutError(Exception):
    """Exception for when a timeout occurs."""
