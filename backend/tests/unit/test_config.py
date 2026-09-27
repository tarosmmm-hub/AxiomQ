from __future__ import annotations

import pytest
from pydantic import ValidationError

from axiomq_api.core.config import (
    INSECURE_DEV_SECRET,
    EmailBackend,
    Environment,
    RateLimitBackend,
    Settings,
)


def test_rejects_short_secret() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(secret_key="short")  # type: ignore[arg-type]


def test_production_refuses_insecure_defaults() -> None:
    with pytest.raises(ValidationError) as exc:
        Settings(
            env=Environment.PRODUCTION,
            secret_key=INSECURE_DEV_SECRET,  # type: ignore[arg-type]
            cookie_secure=False,
            email_backend=EmailBackend.CONSOLE,
            rate_limit_backend=RateLimitBackend.MEMORY,
        )
    message = str(exc.value)
    for fragment in ("SECRET_KEY", "COOKIE_SECURE", "EMAIL_BACKEND", "RATE_LIMIT_BACKEND"):
        assert fragment in message


def test_production_accepts_secure_configuration() -> None:
    settings = Settings(
        env=Environment.PRODUCTION,
        secret_key="p" * 48,  # type: ignore[arg-type]
        cookie_secure=True,
        email_backend=EmailBackend.SMTP,
        rate_limit_backend=RateLimitBackend.REDIS,
    )
    assert settings.is_production
