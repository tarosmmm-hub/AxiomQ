from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from axiomq_api.core.clock import FrozenClock
from axiomq_api.core.container import Container
from axiomq_api.core.email import InMemoryEmailSender
from axiomq_api.modules.audit.models import AuditLog
from axiomq_api.modules.identity.cookies import SESSION_COOKIE
from axiomq_api.modules.identity.models import AuthSession, User
from tests.integration.helpers import (
    STRONG_PASSWORD,
    login,
    register,
    register_and_login,
    token_from_last_email,
)

pytestmark = pytest.mark.integration


def audit_actions(container: Container) -> list[str]:
    with container.session_factory() as db:
        return list(db.execute(select(AuditLog.action).order_by(AuditLog.occurred_at)).scalars())


# ------------------------------------------------------------------ registration
def test_register_creates_user_workspace_and_free_plan(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register(client, email="  Ana@Example.com ")
    assert len(outbox.outbox) == 1
    assert outbox.outbox[0].to == "ana@example.com"
    assert "/verify-email?token=" in outbox.outbox[0].text
    # Registration does not log in (anti-enumeration: same response for existing emails).
    assert SESSION_COOKIE not in client.cookies

    assert login(client, email="ANA@example.com").status_code == 200
    me = client.get("/api/v1/me").json()
    assert me["email"] == "ana@example.com"
    assert me["display_name"] == "Ana"
    assert me["email_verified"] is False

    workspaces = client.get("/api/v1/me/workspaces").json()
    assert len(workspaces) == 1
    assert workspaces[0]["kind"] == "PERSONAL"
    assert workspaces[0]["role"] == "OWNER"
    assert workspaces[0]["plan"] == "FREE"


def test_register_existing_email_is_indistinguishable(client, outbox, container) -> None:  # type: ignore[no-untyped-def]
    register(client)
    first = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ana@example.com",
            "password": "another-strong-passphrase",
            "display_name": "Impostor",
        },
    )
    assert first.status_code == 202
    assert first.json()["status"] == "accepted"
    # The mailbox owner is told; no second account, password unchanged.
    assert "already exists" in outbox.outbox[-1].text
    with container.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
    assert login(client, password="another-strong-passphrase").status_code == 401
    assert login(client).status_code == 200


@pytest.mark.parametrize(
    ("password", "fragment"),
    [("short", "at least"), ("password1234", "too common"), ("mariana-rocks-1987", "email")],
)
def test_register_enforces_password_policy(client, password: str, fragment: str) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "mariana@example.com", "password": password, "display_name": "Mariana"},
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["errors"][0]["field"] == "password"
    assert fragment in body["errors"][0]["message"]


def test_register_validates_email_and_name(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": STRONG_PASSWORD, "display_name": "   "},
    )
    assert response.status_code == 422
    fields = {e["field"] for e in response.json()["errors"]}
    assert {"email", "display_name"} <= fields


# ------------------------------------------------------------------ login / session
def test_login_sets_hardened_cookies(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    response = login(client)
    assert response.status_code == 200
    set_cookie = " | ".join(response.headers.get_list("set-cookie")).lower()
    assert "axq_session=" in set_cookie
    assert "httponly" in set_cookie.split("axq_session=")[1].split("|")[0]
    assert "samesite=lax" in set_cookie


def test_session_token_is_stored_hashed(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    raw = client.cookies.get(SESSION_COOKIE)
    with container.session_factory() as db:
        stored = db.execute(select(AuthSession.token_hash)).scalars().all()
    assert raw not in stored
    assert len(stored) == 1


def test_login_failure_is_generic_and_audited(client, container) -> None:  # type: ignore[no-untyped-def]
    register(client)
    wrong_password = login(client, password="wrong-password-value")
    unknown_user = login(client, email="nobody@example.com")
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["title"] == unknown_user.json()["title"]
    assert audit_actions(container).count("auth.login_failed") == 2


def test_me_requires_authentication(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["type"].endswith("/not_authenticated")


def test_logout_revokes_session_server_side(client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    stolen = client.cookies.get(SESSION_COOKIE)
    assert client.post("/api/v1/auth/logout").status_code == 204
    # Re-using the old cookie value must not work even if the browser kept it.
    client.cookies.set(SESSION_COOKIE, stolen)
    assert client.get("/api/v1/me").status_code == 401


def test_expired_session_is_rejected(client, clock: FrozenClock, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    clock.advance(timedelta(hours=container.settings.session_ttl_hours, seconds=1))
    assert client.get("/api/v1/me").status_code == 401


def test_disabled_user_cannot_use_session_or_login(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    with container.session_factory() as db:
        user = db.execute(select(User)).scalar_one()
        user.disabled_at = container.clock.now()
        db.commit()
    assert client.get("/api/v1/me").status_code == 401
    assert login(client).status_code == 401


def test_login_is_rate_limited_per_email(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    statuses = [login(client, password="wrong-password-value").status_code for _ in range(11)]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429
    blocked = login(client)  # even the right password is blocked during the window
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


# ------------------------------------------------------------------ profile / password
def test_update_profile(client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    response = client.patch("/api/v1/me", json={"display_name": "  Ana   María "})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Ana María"


def test_change_password_revokes_other_sessions(client, make_client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    other = make_client()
    assert login(other).status_code == 200
    response = client.post(
        "/api/v1/me/password",
        json={"current_password": STRONG_PASSWORD, "new_password": "a-brand-new-passphrase"},
    )
    assert response.status_code == 204
    assert client.get("/api/v1/me").status_code == 200  # current session kept
    assert other.get("/api/v1/me").status_code == 401  # other sessions revoked
    assert login(other, password="a-brand-new-passphrase").status_code == 200


def test_change_password_requires_current_password(client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    response = client.post(
        "/api/v1/me/password",
        json={"current_password": "wrong-password-value", "new_password": "a-brand-new-passphrase"},
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "current_password"


# ------------------------------------------------------------------ password reset
def test_password_reset_full_flow(client, outbox: InMemoryEmailSender, make_client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    response = client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    assert response.status_code == 202
    token = token_from_last_email(outbox, "/reset-password")

    anon = make_client()
    confirm = anon.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "reset-to-this-passphrase"},
    )
    assert confirm.status_code == 204
    # All sessions revoked, old password invalid, new one works, email now verified.
    assert client.get("/api/v1/me").status_code == 401
    assert login(anon).status_code == 401
    assert login(anon, password="reset-to-this-passphrase").status_code == 200
    assert anon.get("/api/v1/me").json()["email_verified"] is True


def test_password_reset_token_is_single_use(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register(client)
    client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    token = token_from_last_email(outbox, "/reset-password")
    body = {"token": token, "new_password": "reset-to-this-passphrase"}
    assert client.post("/api/v1/auth/password-reset/confirm", json=body).status_code == 204
    again = client.post("/api/v1/auth/password-reset/confirm", json=body)
    assert again.status_code == 400
    assert again.json()["type"].endswith("/invalid_token")


def test_password_reset_token_expires(client, outbox, clock: FrozenClock, container) -> None:  # type: ignore[no-untyped-def]
    register(client)
    client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    token = token_from_last_email(outbox, "/reset-password")
    clock.advance(timedelta(minutes=container.settings.password_reset_ttl_minutes, seconds=1))
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "reset-to-this-passphrase"},
    )
    assert response.status_code == 400


def test_new_reset_request_revokes_previous_token(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register(client)
    client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    first = token_from_last_email(outbox, "/reset-password")
    client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    second = token_from_last_email(outbox, "/reset-password")
    assert first != second
    body = {"token": first, "new_password": "reset-to-this-passphrase"}
    assert client.post("/api/v1/auth/password-reset/confirm", json=body).status_code == 400
    body["token"] = second
    assert client.post("/api/v1/auth/password-reset/confirm", json=body).status_code == 204


def test_password_reset_for_unknown_email_looks_identical(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register(client)
    sent_before = len(outbox.outbox)
    known = client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    unknown = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "ghost@example.com"}
    )
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(outbox.outbox) == sent_before + 1


def test_password_reset_rejects_weak_new_password(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register(client)
    client.post("/api/v1/auth/password-reset/request", json={"email": "ana@example.com"})
    token = token_from_last_email(outbox, "/reset-password")
    response = client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "short"}
    )
    assert response.status_code == 422
    # Failed request rolled back: the token is still usable.
    ok = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "reset-to-this-passphrase"},
    )
    assert ok.status_code == 204


# ------------------------------------------------------------------ email verification
def test_email_verification_flow(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    token = token_from_last_email(outbox, "/verify-email")
    assert client.post("/api/v1/auth/email/verify", json={"token": token}).status_code == 204
    assert client.get("/api/v1/me").json()["email_verified"] is True
    assert client.post("/api/v1/auth/email/verify", json={"token": token}).status_code == 400


def test_resend_verification_invalidates_previous_link(client, outbox) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    first = token_from_last_email(outbox, "/verify-email")
    assert client.post("/api/v1/auth/email/resend").status_code == 204
    second = token_from_last_email(outbox, "/verify-email")
    assert client.post("/api/v1/auth/email/verify", json={"token": first}).status_code == 400
    assert client.post("/api/v1/auth/email/verify", json={"token": second}).status_code == 204


# ------------------------------------------------------------------ audit trail
def test_security_events_are_audited(client, outbox, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    client.post("/api/v1/auth/logout")
    actions = audit_actions(container)
    assert actions == ["user.registered", "auth.login_succeeded", "auth.logout"]
