from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from axiomq_api.core.deps import ContainerDep

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(container: ContainerDep) -> JSONResponse:
    """Readiness: dependencies reachable."""
    checks: dict[str, str] = {}
    try:
        with container.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.exception("readiness_database_failed")
        checks["database"] = "error"
    if container.redis is not None:
        try:
            container.redis.ping()
            checks["redis"] = "ok"
        except Exception:
            logger.exception("readiness_redis_failed")
            checks["redis"] = "error"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        {"status": "ok" if ok else "error", "checks": checks}, status_code=200 if ok else 503
    )
