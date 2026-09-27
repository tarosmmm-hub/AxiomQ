from __future__ import annotations

from fastapi import Response

from axiomq_api.core.config import Settings
from axiomq_api.core.middleware import CSRF_COOKIE
from axiomq_api.core.security import create_csrf_token

SESSION_COOKIE = "axq_session"


def set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    # Relative Max-Age (not an absolute Expires) so the browser clock does not matter; the
    # server-side expiry in ``sessions.expires_at`` is authoritative.
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, secure=settings.cookie_secure, samesite="lax", path="/"
    )


def issue_csrf_cookie(response: Response, settings: Settings) -> str:
    """The CSRF cookie is readable by JS on purpose (double-submit pattern)."""
    token = create_csrf_token(settings.secret_key.get_secret_value())
    response.set_cookie(
        CSRF_COOKIE, token, httponly=False, secure=settings.cookie_secure, samesite="lax", path="/"
    )
    return token
