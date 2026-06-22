class NotionCliError(Exception):
    """Base error for notion-cli."""


class ConfigError(NotionCliError):
    """Raised when project configuration is missing or invalid."""


class EnvironmentError(NotionCliError):
    """Raised when local tools or authentication are unavailable."""


class RuntimeCommandError(NotionCliError):
    """Raised when `ntn` returns a non-zero exit code."""
