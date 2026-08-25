"""FastAPI application entry point.

Loads the services configuration, builds a checker for each declared service,
and exposes a dedicated health check endpoint per service at
``/service/{name}/health``.
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.checkers.base import BaseChecker
from app.config import load_services_config
from app.exceptions import ConfigurationError
from app.models import HealthStatus
from app.registry import build_checker_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("health_watch")


def register_service_route(app: FastAPI, checker: BaseChecker) -> None:
    """Bind a single ``/service/{name}/health`` route to the given checker.

    Defined as its own function (rather than inline in a loop) so each route's
    closure captures its own checker instead of the loop variable.
    """

    async def service_health() -> JSONResponse:
        result = await checker.check()
        status_code = 200 if result.status is HealthStatus.HEALTHY else 503
        return JSONResponse(content=result.model_dump(mode="json"), status_code=status_code)

    app.add_api_route(
        path=f"/service/{checker.name}/health",
        endpoint=service_health,
        methods=["GET"],
        name=f"health_{checker.name}",
        summary=f"Health check for '{checker.name}' ({checker.service_type})",
        tags=["services"],
    )


def create_app() -> FastAPI:
    services_file = load_services_config()
    checkers = build_checker_registry(services_file)

    app = FastAPI(
        title="Health Watch",
        description="Exposes a per-service health check endpoint, driven by a YAML configuration file.",
    )

    @app.get("/health", tags=["meta"], summary="Liveness check for this application itself")
    def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/services", tags=["meta"], summary="List all configured services")
    def list_services() -> list[dict[str, str]]:
        return [{"name": checker.name, "type": checker.service_type} for checker in checkers.values()]

    for checker in checkers.values():
        register_service_route(app, checker)

    logger.info("Loaded %d service(s): %s", len(checkers), ", ".join(sorted(checkers)) or "none")
    return app


try:
    app = create_app()
except ConfigurationError as exc:
    logger.error("Failed to start Health Watch: %s", exc)
    sys.exit(1)
