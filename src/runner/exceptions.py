class CommandError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class TimeoutError(Exception):
    pass
