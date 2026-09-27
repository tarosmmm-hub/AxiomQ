"""HTTP middlewares: request id, security headers and CSRF enforcement."""

from __future__ import annotations

import re
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from axiomq_api.core.errors import problem
from axiomq_api.core.logging import request_id_var
from axiomq_api.core.security import verify_csrf_token

CSRF_COOKIE = "axq_csrf"
CSRF_HEADER = "x-axiomq-csrf"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

Handler = Callable[[Request], Awaitable[Response]]


def install_middlewares(app: FastAPI, *, secret: str, hsts: bool, docs_paths: set[str]) -> None:
    @app.middleware("http")
    async def csrf_protection(request: Request, call_next: Handler) -> Response:
        needs_check = request.method in UNSAFE_METHODS and request.url.path.startswith("/api/")
        if needs_check and not verify_csrf_token(
            secret, request.cookies.get(CSRF_COOKIE), request.headers.get(CSRF_HEADER)
        ):
            return problem(
                403, "csrf_failed", "CSRF validation failed", "Missing or invalid CSRF token."
            )
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Handler) -> Response:
        response = await call_next(request)
        headers = dict(SECURITY_HEADERS)
        if request.url.path in docs_paths:
            # Swagger UI (non-production only) needs scripts/styles from its CDN.
            headers.pop("Content-Security-Policy")
        if request.url.path.startswith("/api/"):
            headers["Cache-Control"] = "no-store"
        if hsts:
            headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        for key, value in headers.items():
            response.headers.setdefault(key, value)
        return response

    @app.middleware("http")
    async def request_id(request: Request, call_next: Handler) -> Response:
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response
