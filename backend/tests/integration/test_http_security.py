from __future__ import annotations

import pytest

from axiomq_api.core.container import build_container
from axiomq_api.core.middleware import CSRF_COOKIE, CSRF_HEADER
from axiomq_api.main import create_app
from tests.conftest import ApiClient, make_settings
from tests.integration.helpers import STRONG_PASSWORD, register

pytestmark = pytest.mark.integration


def test_mutation_without_csrf_is_rejected(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/login",
        headers={CSRF_HEADER: ""},
        json={"email": "a@example.com", "password": "x"},
    )
    assert response.status_code == 403
    assert response.json()["type"].endswith("/csrf_failed")


def test_csrf_header_must_match_cookie(client) -> None:  # type: ignore[no-untyped-def]
    client.csrf()
    response = client.post(
        "/api/v1/auth/login",
        headers={CSRF_HEADER: "forged.value"},
        json={"email": "a@example.com", "password": "x"},
    )
    assert response.status_code == 403


def test_csrf_token_rotates_on_login(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    before = client.cookies.get(CSRF_COOKIE)
    client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": STRONG_PASSWORD}
    )
    assert client.cookies.get(CSRF_COOKIE) != before


def test_security_headers_present(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/auth/csrf")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_request_id_is_propagated_when_well_formed(client) -> None:  # type: ignore[no-untyped-def]
    assert (
        client.get("/healthz", headers={"x-request-id": "abc-123"}).headers["x-request-id"]
        == "abc-123"
    )
    injected = client.get("/healthz", headers={"x-request-id": "bad value\r\n"})
    assert injected.headers["x-request-id"] != "bad value\r\n"


def test_secure_cookie_flag_when_configured(clean_db, clock, outbox) -> None:  # type: ignore[no-untyped-def]
    container = build_container(make_settings(cookie_secure=True), clock=clock, email_sender=outbox)
    with ApiClient(create_app(container=container), base_url="https://testserver") as c:
        response = c.get("/api/v1/auth/csrf")
        assert "secure" in response.headers["set-cookie"].lower()


def test_unhandled_errors_do_not_leak_details(client) -> None:  # type: ignore[no-untyped-def]
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    client.app.add_api_route("/api/v1/__boom", boom)
    with ApiClient(client.app, raise_server_exceptions=False) as c:
        response = c.get("/api/v1/__boom")
    assert response.status_code == 500
    assert "secret internal detail" not in response.text


def test_health_endpoints(client) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/healthz").json() == {"status": "ok"}
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["checks"]["database"] == "ok"


def test_client_ip_ignores_spoofable_forwarded_header_by_default(client, container) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from axiomq_api.modules.audit.models import AuditLog

    client.post(
        "/api/v1/auth/login",
        headers={"x-forwarded-for": "6.6.6.6"},
        json={"email": "ghost@example.com", "password": "whatever-password"},
    )
    with container.session_factory() as db:
        ip = db.execute(select(AuditLog.ip)).scalar_one()
    assert ip != "6.6.6.6"


def test_client_ip_counts_trusted_hops_from_the_right(clean_db, clock, outbox) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from axiomq_api.modules.audit.models import AuditLog

    container = build_container(
        make_settings(trusted_proxy_hops=1), clock=clock, email_sender=outbox
    )
    with ApiClient(create_app(container=container)) as c:
        # A client-supplied value (left) must not win over what our proxy appended (right).
        c.post(
            "/api/v1/auth/login",
            headers={"x-forwarded-for": "6.6.6.6, 203.0.113.9"},
            json={"email": "ghost@example.com", "password": "whatever-password"},
        )
    with container.session_factory() as db:
        assert db.execute(select(AuditLog.ip)).scalar_one() == "203.0.113.9"
