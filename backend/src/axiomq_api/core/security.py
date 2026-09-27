"""Password hashing, opaque tokens, CSRF token signing and pseudonymisation.

Design notes (ADR-0007):
- Passwords: argon2id. A dummy verification is performed for unknown users so that response
  time does not reveal whether an account exists.
- Opaque tokens (sessions, reset links, verification links): 256 random bits, url-safe encoded.
  Only the SHA-256 digest is stored; a database leak does not yield usable tokens.
- CSRF: signed double-submit token ``<nonce>.<hmac>``; the cookie and header must match and the
  signature must be valid, so a cookie planted by a sibling sub-domain is rejected.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

TOKEN_BYTES = 32


class PasswordHashing:
    def __init__(self, *, time_cost: int, memory_cost_kib: int, parallelism: int) -> None:
        self._hasher = PasswordHasher(
            time_cost=time_cost, memory_cost=memory_cost_kib, parallelism=parallelism
        )
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(16))

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def verify_dummy(self, password: str) -> None:
        """Spend the same time as a real verification (user enumeration protection)."""
        self.verify(self._dummy_hash, password)

    def needs_rehash(self, password_hash: str) -> bool:
        return self._hasher.check_needs_rehash(password_hash)


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hmac_hex(secret: str, message: str) -> str:
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def create_csrf_token(secret: str) -> str:
    nonce = secrets.token_urlsafe(24)
    return f"{nonce}.{_hmac_hex(secret, 'csrf:' + nonce)}"


def verify_csrf_token(secret: str, cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    if not hmac.compare_digest(cookie_value, header_value):
        return False
    nonce, sep, signature = cookie_value.partition(".")
    if not sep or not nonce:
        return False
    return hmac.compare_digest(signature, _hmac_hex(secret, "csrf:" + nonce))


def pseudonymize(secret: str, value: str, *, purpose: str) -> str:
    """Stable keyed pseudonym (HMAC-SHA256). Not reversible without the secret."""
    return _hmac_hex(secret, f"{purpose}:{value}")[:32]
