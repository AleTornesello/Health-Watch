"""Abstract base class shared by all health checkers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.models import HealthCheckResult, HealthStatus


class BaseChecker(ABC):
    """Template-method base class: subclasses implement ``_probe``, this handles
    timing and turns any failure into an ``unhealthy`` result instead of raising.
    """

    #: Pydantic model describing this checker's ``settings`` schema. Subclasses
    #: must override with a concrete ``BaseModel`` so bad config fails fast at startup.
    settings_model: type[BaseModel]

    def __init__(self, name: str, service_type: str, raw_settings: dict[str, Any]) -> None:
        self.name = name
        self.service_type = service_type
        self.settings = self.settings_model.model_validate(raw_settings)

    @abstractmethod
    async def _probe(self) -> str | None:
        """Perform the actual check. Return an optional human-readable detail
        message on success, or raise an exception on failure."""

    async def check(self) -> HealthCheckResult:
        start = time.perf_counter()
        try:
            detail = await self._probe()
            status = HealthStatus.HEALTHY
        except Exception as exc:  # noqa: BLE001 - any probe failure means "unhealthy", not a crash
            detail = str(exc)
            status = HealthStatus.UNHEALTHY
        latency_ms = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            name=self.name,
            type=self.service_type,
            status=status,
            latency_ms=round(latency_ms, 2),
            detail=detail,
        )
