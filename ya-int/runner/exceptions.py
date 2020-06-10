class CommandError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class KeyAlreadyExistsError(CommandError):
    pass


class ContainerNotFoundError(Exception):
    pass


class TimeoutError(Exception):
    pass
