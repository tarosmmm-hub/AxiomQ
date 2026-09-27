"""ASGI entrypoint: ``uvicorn axiomq_api.asgi:app``."""

from axiomq_api.main import create_app

app = create_app()
