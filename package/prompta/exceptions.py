"""Custom exceptions for Prompta CLI."""


class PromptaError(Exception):
    """Base exception for all Prompta CLI errors."""

    pass


class PromptaAPIError(PromptaError):
    """Exception raised for API-related errors."""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(PromptaAPIError):
    """Exception raised for authentication errors (401)."""

    pass


class NotFoundError(PromptaAPIError):
    """Exception raised for not found errors (404)."""

    pass


class ValidationError(PromptaAPIError):
    """Exception raised for validation errors (422)."""

    pass


class ConfigurationError(PromptaError):
    """Exception raised for configuration-related errors."""

    pass


class FileOperationError(PromptaError):
    """Exception raised for file operation errors."""

    pass
