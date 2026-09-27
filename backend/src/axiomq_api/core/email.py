"""Outbound email behind an interface (console in dev, SMTP/Mailpit or a provider in prod)."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailSender:
    """Development only: writes the email to the log (links included)."""

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "email_console",
            extra={"to": message.to, "subject": message.subject, "body": message.text},
        )


class InMemoryEmailSender:
    """Test double that records sent messages."""

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.outbox.append(message)


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        username: str | None,
        password: str | None,
        starttls: bool,
    ) -> None:
        self._host, self._port, self._sender = host, port, sender
        self._username, self._password, self._starttls = username, password, starttls

    def send(self, message: EmailMessage) -> None:
        mime = MimeMessage()
        mime["From"] = self._sender
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            if self._starttls:
                smtp.starttls()
            if self._username and self._password:
                smtp.login(self._username, self._password)
            smtp.send_message(mime)
