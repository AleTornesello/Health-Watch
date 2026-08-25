"""Health checker for HTTP(S) endpoints."""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field

from app.checkers.base import BaseChecker


class HttpSettings(BaseModel):
    url: str
    method: str = "GET"
    timeout: float = 5.0
    expected_status: int = 200
    headers: dict[str, str] = Field(default_factory=dict)


class HttpChecker(BaseChecker):
    settings_model = HttpSettings
    settings: HttpSettings

    async def _probe(self) -> str | None:
        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.request(
                self.settings.method,
                self.settings.url,
                headers=self.settings.headers,
            )

        if response.status_code != self.settings.expected_status:
            raise RuntimeError(
                f"expected status {self.settings.expected_status}, got {response.status_code}"
            )

        return f"HTTP {response.status_code} from {self.settings.url}"
