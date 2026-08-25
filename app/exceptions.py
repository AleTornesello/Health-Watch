"""Application-wide exception types."""


class ConfigurationError(Exception):
    """Raised when the services configuration cannot be located, parsed, or validated."""
