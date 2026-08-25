"""Health checker for Docker containers, via the Docker Engine API."""

from __future__ import annotations

import asyncio

import docker
from pydantic import BaseModel

from app.checkers.base import BaseChecker


class DockerSettings(BaseModel):
    container: str
    base_url: str | None = None  # e.g. "unix://var/run/docker.sock", "npipe:////./pipe/docker_engine"
    timeout: float = 5.0
    expect_running: bool = True


class DockerChecker(BaseChecker):
    settings_model = DockerSettings
    settings: DockerSettings

    async def _probe(self) -> str | None:
        # docker-py is synchronous; run it off the event loop like the other checkers stay non-blocking.
        return await asyncio.to_thread(self._check_container)

    def _check_container(self) -> str:
        # The Docker SDK's timeout is documented and typed as whole seconds.
        timeout_seconds = int(self.settings.timeout)
        client = (
            docker.DockerClient(base_url=self.settings.base_url, timeout=timeout_seconds)
            if self.settings.base_url
            else docker.from_env(timeout=timeout_seconds)
        )
        try:
            container = client.containers.get(self.settings.container)
            status = container.status
            health = container.attrs.get("State", {}).get("Health", {}).get("Status")

            # A container with a HEALTHCHECK is only truly up once Docker reports it healthy -
            # otherwise a running-but-broken process would still read as fine.
            if health is not None and health != "healthy":
                raise RuntimeError(
                    f"container '{self.settings.container}' health is '{health}' (status: {status})"
                )
            if self.settings.expect_running and status != "running":
                raise RuntimeError(f"container '{self.settings.container}' status is '{status}'")

            detail = f"container '{self.settings.container}' is {status}"
            return f"{detail}, health: {health}" if health else detail
        finally:
            client.close()
