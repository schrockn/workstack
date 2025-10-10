"""Custom exceptions for the dev CLI framework."""


class DevCliFrameworkError(Exception):
    """Base exception for all dev CLI framework errors."""

    pass


class CommandLoadError(DevCliFrameworkError):
    """Raised when command loading fails."""

    pass


class ScriptExecutionError(DevCliFrameworkError):
    """Raised when script execution fails."""

    pass
