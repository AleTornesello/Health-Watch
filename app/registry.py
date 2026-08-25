"""Builds the runtime registry of checkers from a validated services file."""

from __future__ import annotations

from app.checkers import create_checker
from app.checkers.base import BaseChecker
from app.exceptions import ConfigurationError
from app.models import ServicesFile


def build_checker_registry(services_file: ServicesFile) -> dict[str, BaseChecker]:
    """Create one checker per service, keyed by service name.

    Fails fast on duplicate names or invalid settings so misconfiguration is
    caught at startup rather than surfacing as a confusing 404 or crash later.
    """
    registry: dict[str, BaseChecker] = {}

    for service in services_file.services:
        if service.name in registry:
            raise ConfigurationError(f"Duplicate service name '{service.name}' in configuration.")
        registry[service.name] = create_checker(service)

    return registry
