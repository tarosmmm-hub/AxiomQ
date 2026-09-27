from __future__ import annotations

from axiomq_api.core.security import (
    PasswordHashing,
    create_csrf_token,
    generate_token,
    hash_token,
    pseudonymize,
    verify_csrf_token,
)

SECRET = "unit-test-secret-0123456789-abcdefghijkl"


def hasher() -> PasswordHashing:
    return PasswordHashing(time_cost=1, memory_cost_kib=8, parallelism=1)


def test_password_hash_roundtrip_and_uses_argon2id() -> None:
    h = hasher()
    digest = h.hash("a long enough passphrase")
    assert digest.startswith("$argon2id$")
    assert h.verify(digest, "a long enough passphrase")
    assert not h.verify(digest, "a long enough passphrasE")


def test_password_hash_is_salted() -> None:
    h = hasher()
    assert h.hash("same password here") != h.hash("same password here")


def test_verify_rejects_garbage_hash_without_raising() -> None:
    assert not hasher().verify("not-a-hash", "whatever")


def test_needs_rehash_when_parameters_change() -> None:
    weak = PasswordHashing(time_cost=1, memory_cost_kib=8, parallelism=1)
    strong = PasswordHashing(time_cost=2, memory_cost_kib=16, parallelism=1)
    assert strong.needs_rehash(weak.hash("some passphrase value"))
    assert not weak.needs_rehash(weak.hash("some passphrase value"))


def test_tokens_are_random_and_only_digest_is_stored() -> None:
    a, b = generate_token(), generate_token()
    assert a != b
    assert len(a) >= 43  # 32 bytes url-safe base64
    assert hash_token(a) == hash_token(a)
    assert hash_token(a) != a
    assert len(hash_token(a)) == 64


def test_csrf_token_valid_when_cookie_and_header_match() -> None:
    token = create_csrf_token(SECRET)
    assert verify_csrf_token(SECRET, token, token)


def test_csrf_rejects_missing_or_mismatched_values() -> None:
    token = create_csrf_token(SECRET)
    other = create_csrf_token(SECRET)
    assert not verify_csrf_token(SECRET, None, token)
    assert not verify_csrf_token(SECRET, token, None)
    assert not verify_csrf_token(SECRET, token, other)


def test_csrf_rejects_forged_signature() -> None:
    nonce = create_csrf_token(SECRET).split(".")[0]
    forged = f"{nonce}.{'0' * 64}"
    assert not verify_csrf_token(SECRET, forged, forged)
    assert not verify_csrf_token(SECRET, "no-dot", "no-dot")
    # A token signed with another secret (e.g. planted by another app) is rejected.
    foreign = create_csrf_token("another-secret-0123456789-abcdefghijklmn")
    assert not verify_csrf_token(SECRET, foreign, foreign)


def test_pseudonymize_is_stable_keyed_and_purpose_bound() -> None:
    a = pseudonymize(SECRET, "user-1", purpose="analytics")
    assert a == pseudonymize(SECRET, "user-1", purpose="analytics")
    assert a != pseudonymize(SECRET, "user-1", purpose="audit")
    assert a != pseudonymize("x" * 40, "user-1", purpose="analytics")
    assert "user-1" not in a
