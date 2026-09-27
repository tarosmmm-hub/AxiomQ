"""Password policy (NIST SP 800-63B inspired: length over composition rules)."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

MIN_LENGTH = 12
MAX_LENGTH = 128


@lru_cache(maxsize=1)
def _common_passwords() -> frozenset[str]:
    text = resources.files("axiomq_api.core").joinpath("common_passwords.txt").read_text("utf-8")
    lines = (line.strip() for line in text.splitlines())
    return frozenset(line.lower() for line in lines if line and not line.startswith("#"))


def password_problems(password: str, *, email: str | None = None) -> list[str]:
    """Return human-readable reasons why ``password`` is not acceptable (empty if acceptable)."""
    problems: list[str] = []
    if len(password) < MIN_LENGTH:
        problems.append(f"Password must be at least {MIN_LENGTH} characters long.")
    if len(password) > MAX_LENGTH:
        problems.append(f"Password must be at most {MAX_LENGTH} characters long.")
    lowered = password.lower()
    if lowered in _common_passwords():
        problems.append("This password is too common.")
    if len(set(password)) < 4:
        problems.append("Password is too repetitive.")
    if email:
        local = email.split("@", 1)[0].lower()
        if lowered == email.lower() or (len(local) >= 4 and local in lowered):
            problems.append("Password must not contain your email address.")
    return problems
