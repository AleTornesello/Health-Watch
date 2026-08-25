"""Registry and factory for health checkers.

Adding a new service type means writing a ``BaseChecker`` subclass and adding
one entry to ``CHECKER_TYPES`` below - no changes needed anywhere else.
"""

from __future__ import annotations

from app.checkers.base import BaseChecker
from app.checkers.docker_checker import DockerChecker
from app.checkers.http_checker import HttpChecker
from app.checkers.postgres_checker import PostgresChecker
from app.checkers.qdrant_checker import QdrantChecker
from app.checkers.tcp_checker import TcpChecker
from app.exceptions import ConfigurationError
from app.models import ServiceDefinition

CHECKER_TYPES: dict[str, type[BaseChecker]] = {
    "http": HttpChecker,
    "tcp": TcpChecker,
    "postgres": PostgresChecker,
    "qdrant": QdrantChecker,
    "docker": DockerChecker,
}


def create_checker(service: ServiceDefinition) -> BaseChecker:
    """Instantiate the checker for a service definition, validating its settings."""
    checker_cls = CHECKER_TYPES.get(service.type)
    if checker_cls is None:
        available = ", ".join(sorted(CHECKER_TYPES)) or "none registered"
        raise ConfigurationError(
            f"Service '{service.name}' has unknown type '{service.type}'. Available types: {available}."
        )

    try:
        return checker_cls(name=service.name, service_type=service.type, raw_settings=service.settings)
    except Exception as exc:  # noqa: BLE001 - surface as a clear configuration error
        raise ConfigurationError(
            f"Service '{service.name}' has invalid settings for type '{service.type}': {exc}"
        ) from exc
