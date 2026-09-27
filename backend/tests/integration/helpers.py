from __future__ import annotations

import re

from axiomq_api.core.email import InMemoryEmailSender

STRONG_PASSWORD = "correct-horse-battery-staple"


def token_from_last_email(outbox: InMemoryEmailSender, path: str) -> str:
    for message in reversed(outbox.outbox):
        match = re.search(re.escape(path) + r"\?token=([A-Za-z0-9_\-]+)", message.text)
        if match:
            return match.group(1)
    raise AssertionError(f"No email with a {path} link")


def register(
    client,
    email: str = "ana@example.com",
    password: str = STRONG_PASSWORD,  # type: ignore[no-untyped-def]
    name: str = "Ana",
) -> None:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "display_name": name}
    )
    assert response.status_code == 202, response.text


def login(client, email: str = "ana@example.com", password: str = STRONG_PASSWORD):  # type: ignore[no-untyped-def]
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def register_and_login(client, email: str = "ana@example.com", name: str = "Ana") -> None:  # type: ignore[no-untyped-def]
    register(client, email=email, name=name)
    response = login(client, email=email)
    assert response.status_code == 200, response.text
