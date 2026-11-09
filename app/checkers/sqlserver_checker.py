"""Health checker for Microsoft SQL Server databases."""

from __future__ import annotations

import asyncio

import pymssql
from pydantic import BaseModel

from app.checkers.base import BaseChecker


class SqlServerSettings(BaseModel):
    host: str
    port: int = 1433
    username: str
    password: str
    database: str
    timeout: float = 5.0


class SqlServerChecker(BaseChecker):
    settings_model = SqlServerSettings
    settings: SqlServerSettings

    async def _probe(self) -> str | None:
        # pymssql is synchronous; run it off the event loop like the other checkers stay non-blocking.
        return await asyncio.to_thread(self._query)

    def _query(self) -> str:
        # pymssql takes whole seconds; login_timeout covers connecting, timeout covers the query.
        timeout_seconds = max(1, int(self.settings.timeout))
        connection = pymssql.connect(
            server=self.settings.host,
            port=str(self.settings.port),
            user=self.settings.username,
            password=self.settings.password,
            database=self.settings.database,
            login_timeout=timeout_seconds,
            timeout=timeout_seconds,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            connection.close()

        return f"connected to database '{self.settings.database}' on {self.settings.host}:{self.settings.port}"
