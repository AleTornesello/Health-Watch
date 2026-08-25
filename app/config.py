"""Locates and loads the services configuration file.

Resolution order:
  1. The path given by the ``HEALTH_WATCH_SERVICES_FILE`` environment variable.
  2. ``services.yaml`` in the project root (the parent of this ``app`` package).

If neither yields a readable, valid file, ``ConfigurationError`` is raised so the
caller can fail fast and exit.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.exceptions import ConfigurationError
from app.models import ServicesFile

SERVICES_FILE_ENV_VAR = "HEALTH_WATCH_SERVICES_FILE"
DEFAULT_SERVICES_FILENAME = "services.yaml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

_ENV_VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(:-(?P<default>[^}]*))?\}")


def resolve_services_path() -> Path:
    """Determine which services file to load, without reading it yet."""
    env_path = os.environ.get(SERVICES_FILE_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()
    return PROJECT_ROOT / DEFAULT_SERVICES_FILENAME


def load_services_config(path: Path | None = None) -> ServicesFile:
    """Read, interpolate, and validate the services file, raising on any failure."""
    path = path or resolve_services_path()

    if not path.is_file():
        raise ConfigurationError(
            f"Services configuration file not found at '{path}'. "
            f"Set the {SERVICES_FILE_ENV_VAR} environment variable or place a "
            f"'{DEFAULT_SERVICES_FILENAME}' file in the project root."
        )

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"Could not read services configuration file '{path}': {exc}") from exc

    try:
        raw_data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Services configuration file '{path}' is not valid YAML: {exc}") from exc

    raw_data = _interpolate_env_vars(raw_data)

    try:
        return ServicesFile.model_validate(raw_data or {})
    except ValidationError as exc:
        raise ConfigurationError(f"Services configuration file '{path}' is invalid:\n{exc}") from exc


def _interpolate_env_vars(value: Any) -> Any:
    """Recursively expand ``${VAR}`` / ``${VAR:-default}`` placeholders in string values.

    Lets secrets (e.g. passwords) be referenced by name instead of stored in plain text.
    """
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name = match.group("name")
            default = match.group("default")
            resolved = os.environ.get(name)
            if resolved is not None:
                return resolved
            if default is not None:
                return default
            raise ConfigurationError(f"Environment variable '{name}' referenced in configuration is not set.")

        return _ENV_VAR_PATTERN.sub(replace, value)
    if isinstance(value, dict):
        return {key: _interpolate_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    return value
