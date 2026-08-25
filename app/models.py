"""Pydantic models describing configuration and health check results."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServiceDefinition(BaseModel):
    """A single monitored service, as declared in the services YAML file."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Unique key used in the API path.")
    type: str = Field(..., min_length=1, description="Checker type, e.g. 'http', 'tcp', 'postgres'.")
    settings: dict[str, Any] = Field(default_factory=dict, description="Checker-specific connection settings.")


class ServicesFile(BaseModel):
    """Root schema of the services YAML file."""

    model_config = ConfigDict(extra="forbid")

    services: list[ServiceDefinition] = Field(default_factory=list)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthCheckResult(BaseModel):
    """Outcome of a single health probe, returned by the API."""

    name: str
    type: str
    status: HealthStatus
    latency_ms: float
    detail: str | None = None
