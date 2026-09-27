from __future__ import annotations

import pytest

from axiomq_api.core.passwords import MAX_LENGTH, MIN_LENGTH, password_problems


def test_accepts_long_uncommon_password() -> None:
    assert password_problems("violet-otter-sings-at-dawn", email="ana@example.com") == []


@pytest.mark.parametrize("length", [0, 1, MIN_LENGTH - 1])
def test_rejects_short(length: int) -> None:
    assert any("at least" in p for p in password_problems(("abcdefghijklmnop" * 2)[:length]))


def test_boundary_lengths() -> None:
    assert not any("at least" in p for p in password_problems("abcdefghijk1"[:MIN_LENGTH]))
    assert any("at most" in p for p in password_problems("abcd" * (MAX_LENGTH // 4) + "e"))


def test_rejects_common_password_case_insensitive() -> None:
    assert "This password is too common." in password_problems("Password1234")


def test_rejects_repetitive() -> None:
    assert "Password is too repetitive." in password_problems("abababababababab")


def test_rejects_password_containing_email_local_part() -> None:
    problems = password_problems("my-name-is-mariana-ok", email="Mariana@example.com")
    assert "Password must not contain your email address." in problems


def test_short_local_part_is_not_checked() -> None:
    # A 2-letter local part would reject too many legitimate passwords.
    assert password_problems("a-perfectly-fine-passphrase", email="al@example.com") == []
