"""Health checker for PostgreSQL databases."""

from __future__ import annotations

import asyncpg
from pydantic import BaseModel

from app.checkers.base import BaseChecker


class PostgresSettings(BaseModel):
    host: str
    port: int = 5432
    username: str
    password: str
    database: str
    timeout: float = 5.0


class PostgresChecker(BaseChecker):
    settings_model = PostgresSettings
    settings: PostgresSettings

    async def _probe(self) -> str | None:
        connection = await asyncpg.connect(
            host=self.settings.host,
            port=self.settings.port,
            user=self.settings.username,
            password=self.settings.password,
            database=self.settings.database,
            timeout=self.settings.timeout,  # type: ignore[arg-type]  # asyncpg accepts float at runtime
        )
        try:
            await connection.fetchval("SELECT 1")
        finally:
            await connection.close()

        return f"connected to database '{self.settings.database}' on {self.settings.host}:{self.settings.port}"
