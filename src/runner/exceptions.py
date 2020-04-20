class CommandError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ContainerNotFoundError(Exception):
    pass


class TimeoutError(Exception):
    pass
