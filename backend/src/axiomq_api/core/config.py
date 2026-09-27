"""Application settings (12-factor: everything comes from the environment).

All variables use the ``AXIOMQ_`` prefix; see ``.env.example`` at the repository root.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_SECRET = "dev-insecure-secret-change-me-0123456789abcdef"  # noqa: S105


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class EmailBackend(StrEnum):
    CONSOLE = "console"
    SMTP = "smtp"
    MEMORY = "memory"


class RateLimitBackend(StrEnum):
    REDIS = "redis"
    MEMORY = "memory"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AXIOMQ_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    env: Environment = Environment.DEVELOPMENT
    app_name: str = "AxiomQ"

    database_url: str = "postgresql+psycopg://axiomq:axiomq@localhost:5432/axiomq"
    redis_url: str = "redis://localhost:6379/0"

    # Used to sign CSRF tokens and to pseudonymise analytics/audit identifiers.
    secret_key: SecretStr = SecretStr(INSECURE_DEV_SECRET)

    frontend_url: str = "http://localhost:3000"

    cookie_secure: bool = True
    session_ttl_hours: int = Field(default=24 * 14, ge=1)
    password_reset_ttl_minutes: int = Field(default=30, ge=5, le=24 * 60)
    email_verification_ttl_hours: int = Field(default=48, ge=1)
    require_email_verification: bool = True

    # argon2id parameters (OWASP recommended minimum: m=19 MiB, t=2, p=1).
    argon2_time_cost: int = Field(default=3, ge=1)
    argon2_memory_cost_kib: int = Field(default=65536, ge=8)
    argon2_parallelism: int = Field(default=4, ge=1)

    email_backend: EmailBackend = EmailBackend.CONSOLE
    email_from: str = "AxiomQ <no-reply@axiomq.local>"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = False

    rate_limit_backend: RateLimitBackend = RateLimitBackend.REDIS
    # Number of reverse proxies in front of the API that append to X-Forwarded-For (e.g. 1 for
    # the Next.js proxy, 2 for load balancer + Next.js). 0 = ignore the header (direct access).
    # The client IP is taken counting from the right, so clients cannot spoof it.
    trusted_proxy_hops: int = Field(default=0, ge=0, le=5)

    log_level: str = "INFO"
    log_json: bool = True

    @model_validator(mode="after")
    def _validate_security(self) -> Self:
        secret = self.secret_key.get_secret_value()
        if len(secret) < 32:
            raise ValueError("AXIOMQ_SECRET_KEY must be at least 32 characters")
        if self.env is Environment.PRODUCTION:
            problems = []
            if secret == INSECURE_DEV_SECRET:
                problems.append("AXIOMQ_SECRET_KEY must be set")
            if not self.cookie_secure:
                problems.append("AXIOMQ_COOKIE_SECURE must be true")
            if self.email_backend is not EmailBackend.SMTP:
                problems.append("AXIOMQ_EMAIL_BACKEND must be smtp")
            if self.rate_limit_backend is not RateLimitBackend.REDIS:
                problems.append("AXIOMQ_RATE_LIMIT_BACKEND must be redis")
            if problems:
                raise ValueError("Insecure production configuration: " + "; ".join(problems))
        return self

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()
