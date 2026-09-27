"""Application factory."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from axiomq_api import __version__
from axiomq_api.core.config import Environment, Settings, get_settings
from axiomq_api.core.container import Container, build_container
from axiomq_api.core.errors import install_error_handlers
from axiomq_api.core.logging import configure_logging
from axiomq_api.core.middleware import install_middlewares
from axiomq_api.modules.billing.router import router as billing_router
from axiomq_api.modules.health.router import router as health_router
from axiomq_api.modules.identity.router import auth_router, me_router
from axiomq_api.modules.workspaces.router import router as workspaces_router

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or (container.settings if container else get_settings())
    container = container or build_container(settings)
    if settings.env is not Environment.TEST:
        configure_logging(settings.log_level, json_output=settings.log_json)

    docs_enabled = not settings.is_production
    app = FastAPI(
        title="AxiomQ API",
        version=__version__,
        openapi_url=f"{API_PREFIX}/openapi.json" if docs_enabled else None,
        docs_url=f"{API_PREFIX}/docs" if docs_enabled else None,
        redoc_url=None,
    )
    app.state.container = container

    install_error_handlers(app)
    install_middlewares(
        app,
        secret=container.secret,
        hsts=settings.is_production,
        docs_paths={f"{API_PREFIX}/docs"} if docs_enabled else set(),
    )

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(auth_router)
    api.include_router(me_router)
    api.include_router(workspaces_router)
    api.include_router(billing_router)
    app.include_router(api)
    app.include_router(health_router)
    return app
