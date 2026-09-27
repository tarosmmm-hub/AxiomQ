"""Application errors rendered as RFC 9457 ``application/problem+json``."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"
PROBLEM_BASE = "https://axiomq.dev/problems/"


class AppError(Exception):
    status_code: int = 400
    code: str = "bad_request"
    title: str = "Bad request"

    def __init__(
        self,
        detail: str | None = None,
        *,
        extra: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.extra = extra or {}
        self.headers = headers or {}


class NotAuthenticated(AppError):
    status_code = 401
    code = "not_authenticated"
    title = "Authentication required"


class InvalidCredentials(AppError):
    status_code = 401
    code = "invalid_credentials"
    title = "Invalid email or password"


class PermissionDenied(AppError):
    status_code = 403
    code = "permission_denied"
    title = "Permission denied"


class CsrfFailed(AppError):
    status_code = 403
    code = "csrf_failed"
    title = "CSRF validation failed"


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    title = "Resource not found"


class Conflict(AppError):
    status_code = 409
    code = "conflict"
    title = "Conflict"


class InvalidToken(AppError):
    status_code = 400
    code = "invalid_token"
    title = "The link is invalid or has expired"


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_failed"
    title = "Validation failed"

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message, extra={"errors": [{"field": field, "message": message}]})


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"
    title = "Too many requests"

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            "Too many attempts. Try again later.",
            extra={"retry_after": retry_after_seconds},
            headers={"Retry-After": str(retry_after_seconds)},
        )


class FeatureNotAvailable(AppError):
    status_code = 403
    code = "entitlement_required"
    title = "Your plan does not include this feature"


class QuotaExceeded(AppError):
    status_code = 403
    code = "quota_exceeded"
    title = "Plan limit reached"


def problem(
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    extra: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"type": PROBLEM_BASE + code, "title": title, "status": status}
    if detail:
        body["detail"] = detail
    if extra:
        body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return problem(exc.status_code, exc.code, exc.title, exc.detail, exc.extra, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(p) for p in err.get("loc", ()) if p != "body"),
                "message": err.get("msg", "Invalid value"),
            }
            for err in exc.errors()
        ]
        return problem(422, "validation_failed", "Validation failed", extra={"errors": errors})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return problem(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", exc_info=exc)
        return problem(500, "internal_error", "Internal server error")
