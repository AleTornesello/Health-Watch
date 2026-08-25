"""Health checker for generic TCP reachability (caches, queues, raw sockets, ...)."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel

from app.checkers.base import BaseChecker


class TcpSettings(BaseModel):
    host: str
    port: int
    timeout: float = 5.0


class TcpChecker(BaseChecker):
    settings_model = TcpSettings
    settings: TcpSettings

    async def _probe(self) -> str | None:
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.settings.host, self.settings.port),
                timeout=self.settings.timeout,
            )
        except TimeoutError as exc:
            raise TimeoutError(
                f"timed out after {self.settings.timeout}s connecting to "
                f"{self.settings.host}:{self.settings.port}"
            ) from exc

        writer.close()
        await writer.wait_closed()
        return f"connected to {self.settings.host}:{self.settings.port}"
