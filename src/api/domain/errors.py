class InvalidPasRequestError(Exception):
    """Raised when a PAS $submit request body fails structural checks."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
