"""Application specific exceptions.

Kept free of any Flask import so that the GitHub client stays testable in
isolation and cannot create circular imports with the application module.
"""


class GitHubError(Exception):
    """Raised when GitHub cannot serve the public data that was requested.

    Args:
        status_code (int): HTTP status code to expose to the visitor.
        message (str): human readable description of the failure.
    """

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
