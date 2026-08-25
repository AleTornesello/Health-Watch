"""Health checker for Qdrant vector database instances."""

from __future__ import annotations

import logging

import httpx
from pydantic import BaseModel

from app.checkers.base import BaseChecker

logger = logging.getLogger("health_watch.qdrant")


class QdrantSettings(BaseModel):
    host: str
    port: int = 6333
    https: bool = False
    api_key: str | None = None
    collection: str | None = None
    timeout: float = 5.0


class QdrantChecker(BaseChecker):
    settings_model = QdrantSettings
    settings: QdrantSettings

    async def _probe(self) -> str | None:
        scheme = "https" if self.settings.https else "http"
        base_url = f"{scheme}://{self.settings.host}:{self.settings.port}"
        headers = {"api-key": self.settings.api_key} if self.settings.api_key else {}
        # If a collection is given, checking it also proves the API key (if any) is valid.
        path = f"/collections/{self.settings.collection}" if self.settings.collection else "/healthz"

        logger.debug(
            "[%s] requesting %s%s (timeout=%s, headers=%s)",
            self.name, base_url, path, self.settings.timeout, list(headers),
        )

        async with httpx.AsyncClient(base_url=base_url, timeout=self.settings.timeout, headers=headers) as client:
            response = await client.get(path)

        logger.debug(
            "[%s] response status=%s headers=%s body=%s",
            self.name, response.status_code, dict(response.headers), response.text,
        )

        if response.status_code != 200:
            raise RuntimeError(f"expected status 200 from {path}, got {response.status_code}")

        if self.settings.collection:
            return f"collection '{self.settings.collection}' reachable on {base_url}"
        return f"Qdrant reachable on {base_url}"
