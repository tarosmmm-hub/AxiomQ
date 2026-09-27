"""Identity use cases: registration, login, sessions, password reset, email verification.

Anti-enumeration: registration, login and password-reset responses do not reveal whether an
email is registered. Registration always answers 202 and sends either a verification email or an
"account already exists" notice to the address.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from axiomq_api.core import rate_limit as rl
from axiomq_api.core.container import Container
from axiomq_api.core.deps import RequestMeta, enforce_rate_limit
from axiomq_api.core.email import EmailMessage
from axiomq_api.core.errors import InvalidCredentials, InvalidToken, ValidationFailed
from axiomq_api.core.passwords import password_problems
from axiomq_api.core.security import generate_token, hash_token, pseudonymize
from axiomq_api.db.session import UnitOfWork
from axiomq_api.modules.audit.service import AuditAction, AuditService
from axiomq_api.modules.billing.service import create_free_subscription
from axiomq_api.modules.identity.models import AuthSession, TokenPurpose, User, UserToken
from axiomq_api.modules.workspaces.service import create_personal_workspace


def normalize_email(email: str) -> str:
    return email.strip().lower()


@dataclass(frozen=True)
class IssuedSession:
    token: str
    expires_at: datetime


class IdentityService:
    def __init__(self, container: Container, uow: UnitOfWork, meta: RequestMeta) -> None:
        self.c = container
        self.uow = uow
        self.db: Session = uow.session
        self.meta = meta
        self.audit = AuditService(container.clock)

    # ---------------------------------------------------------------- helpers
    def _now(self) -> datetime:
        return self.c.clock.now()

    def _ip_key(self) -> str:
        return self.meta.ip or "unknown"

    def _email_key(self, email: str) -> str:
        return pseudonymize(self.c.secret, email, purpose="ratelimit")

    def _check_password(self, password: str, email: str) -> None:
        problems = password_problems(password, email=email)
        if problems:
            raise ValidationFailed("password", " ".join(problems))

    def _user_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def _issue_user_token(self, user: User, purpose: TokenPurpose, ttl: timedelta) -> str:
        now = self._now()
        self.db.execute(
            update(UserToken)
            .where(
                UserToken.user_id == user.id,
                UserToken.purpose == purpose,
                UserToken.used_at.is_(None),
                UserToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        token = generate_token()
        self.db.add(
            UserToken(
                user_id=user.id,
                purpose=purpose,
                token_hash=hash_token(token),
                expires_at=now + ttl,
            )
        )
        return token

    def _consume_user_token(self, token: str, purpose: TokenPurpose) -> User:
        now = self._now()
        row = self.db.execute(
            select(UserToken)
            .where(UserToken.token_hash == hash_token(token), UserToken.purpose == purpose)
            .with_for_update()
        ).scalar_one_or_none()
        if row is None or row.used_at or row.revoked_at or row.expires_at <= now:
            raise InvalidToken()
        user = self.db.get(User, row.user_id)
        if user is None or user.disabled_at is not None:
            raise InvalidToken()
        row.used_at = now
        return user

    def _send_later(self, to: str, subject: str, text: str) -> None:
        sender = self.c.email_sender
        message = EmailMessage(to=to, subject=subject, text=text)
        self.uow.defer(lambda: sender.send(message))

    def _link(self, path: str, token: str) -> str:
        return f"{self.c.settings.frontend_url.rstrip('/')}{path}?token={token}"

    def _revoke_sessions(self, user_id: uuid.UUID, *, except_id: uuid.UUID | None = None) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=self._now())
        )
        if except_id is not None:
            stmt = stmt.where(AuthSession.id != except_id)
        self.db.execute(stmt)

    def _create_session(self, user: User) -> IssuedSession:
        token = generate_token()
        expires_at = self._now() + timedelta(hours=self.c.settings.session_ttl_hours)
        self.db.add(
            AuthSession(
                user_id=user.id,
                token_hash=hash_token(token),
                expires_at=expires_at,
                ip=self.meta.ip,
                user_agent=self.meta.user_agent,
            )
        )
        return IssuedSession(token=token, expires_at=expires_at)

    def _send_verification(self, user: User) -> None:
        token = self._issue_user_token(
            user,
            TokenPurpose.EMAIL_VERIFICATION,
            timedelta(hours=self.c.settings.email_verification_ttl_hours),
        )
        self._send_later(
            user.email,
            "Verify your AxiomQ email",
            "Confirm your email address to finish setting up your AxiomQ account:\n\n"
            f"{self._link('/verify-email', token)}\n\n"
            f"The link expires in {self.c.settings.email_verification_ttl_hours} hours. "
            "If you did not create an account, ignore this message.",
        )

    # ---------------------------------------------------------------- use cases
    def register(self, *, email: str, password: str, display_name: str) -> None:
        enforce_rate_limit(self.c, rl.REGISTER_PER_IP, self._ip_key())
        email = normalize_email(email)
        self._check_password(password, email)
        existing = self._user_by_email(email)
        if existing is not None:
            # Same expensive work as the new-account path so timing does not reveal the account.
            self.c.passwords.hash(password)
            self.audit.record(
                self.db,
                AuditAction.REGISTER_EXISTING_EMAIL,
                actor_user_id=existing.id,
                meta=self.meta,
            )
            self._send_later(
                email,
                "AxiomQ sign-up attempt",
                "Someone tried to create an AxiomQ account with this email address, but an "
                "account already exists.\n\n"
                f"Sign in: {self.c.settings.frontend_url.rstrip('/')}/login\n"
                f"Forgot your password? {self.c.settings.frontend_url.rstrip('/')}/forgot-password"
                "\n\nIf this was not you, you can ignore this message.",
            )
            return
        user = User(
            email=email, password_hash=self.c.passwords.hash(password), display_name=display_name
        )
        self.db.add(user)
        self.db.flush()
        workspace = create_personal_workspace(self.db, owner_id=user.id, display_name=display_name)
        create_free_subscription(self.db, workspace.id)
        self.audit.record(
            self.db,
            AuditAction.USER_REGISTERED,
            actor_user_id=user.id,
            target_type="user",
            target_id=str(user.id),
            meta=self.meta,
        )
        self._send_verification(user)

    def login(self, *, email: str, password: str) -> IssuedSession:
        email = normalize_email(email)
        enforce_rate_limit(self.c, rl.LOGIN_PER_IP, self._ip_key())
        enforce_rate_limit(self.c, rl.LOGIN_PER_EMAIL, self._email_key(email))
        user = self._user_by_email(email)
        if user is None:
            self.c.passwords.verify_dummy(password)
        ok = (
            user is not None
            and user.disabled_at is None
            and self.c.passwords.verify(user.password_hash, password)
        )
        if not ok or user is None:
            self.audit.record_independent(
                self.c.session_factory,
                AuditAction.LOGIN_FAILED,
                actor_user_id=user.id if user else None,
                meta=self.meta,
                details={"email_ref": pseudonymize(self.c.secret, email, purpose="audit")},
            )
            raise InvalidCredentials()
        if self.c.passwords.needs_rehash(user.password_hash):
            user.password_hash = self.c.passwords.hash(password)
        user.last_login_at = self._now()
        issued = self._create_session(user)
        self.audit.record(
            self.db, AuditAction.LOGIN_SUCCEEDED, actor_user_id=user.id, meta=self.meta
        )
        return issued

    def logout(self, session: AuthSession) -> None:
        session.revoked_at = self._now()
        self.audit.record(
            self.db, AuditAction.LOGOUT, actor_user_id=session.user_id, meta=self.meta
        )

    def authenticate(self, token: str | None) -> tuple[User, AuthSession] | None:
        if not token:
            return None
        row = self.db.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .where(AuthSession.token_hash == hash_token(token))
        ).first()
        if row is None:
            return None
        session, user = row
        if session.revoked_at is not None or session.expires_at <= self._now():
            return None
        if user.disabled_at is not None:
            return None
        return user, session

    def request_password_reset(self, *, email: str) -> None:
        email = normalize_email(email)
        enforce_rate_limit(self.c, rl.RESET_PER_IP, self._ip_key())
        enforce_rate_limit(self.c, rl.RESET_PER_EMAIL, self._email_key(email))
        user = self._user_by_email(email)
        if user is None or user.disabled_at is not None:
            return
        token = self._issue_user_token(
            user,
            TokenPurpose.PASSWORD_RESET,
            timedelta(minutes=self.c.settings.password_reset_ttl_minutes),
        )
        self.audit.record(
            self.db, AuditAction.PASSWORD_RESET_REQUESTED, actor_user_id=user.id, meta=self.meta
        )
        self._send_later(
            user.email,
            "Reset your AxiomQ password",
            "Use this link to choose a new password:\n\n"
            f"{self._link('/reset-password', token)}\n\n"
            f"The link expires in {self.c.settings.password_reset_ttl_minutes} minutes and can "
            "be used once. If you did not request it, ignore this message.",
        )

    def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        user = self._consume_user_token(token, TokenPurpose.PASSWORD_RESET)
        self._check_password(new_password, user.email)
        user.password_hash = self.c.passwords.hash(new_password)
        if user.email_verified_at is None:
            # Receiving the reset link proves control of the mailbox.
            user.email_verified_at = self._now()
        self._revoke_sessions(user.id)
        self.audit.record(
            self.db, AuditAction.PASSWORD_RESET_COMPLETED, actor_user_id=user.id, meta=self.meta
        )

    def verify_email(self, *, token: str) -> None:
        user = self._consume_user_token(token, TokenPurpose.EMAIL_VERIFICATION)
        if user.email_verified_at is None:
            user.email_verified_at = self._now()
            self.audit.record(
                self.db, AuditAction.EMAIL_VERIFIED, actor_user_id=user.id, meta=self.meta
            )

    def resend_verification(self, user: User) -> None:
        enforce_rate_limit(self.c, rl.VERIFY_RESEND_PER_USER, str(user.id))
        if user.email_verified_at is None:
            self._send_verification(user)

    def change_password(
        self, user: User, session: AuthSession, *, current_password: str, new_password: str
    ) -> None:
        if not self.c.passwords.verify(user.password_hash, current_password):
            raise ValidationFailed("current_password", "Current password is incorrect.")
        self._check_password(new_password, user.email)
        user.password_hash = self.c.passwords.hash(new_password)
        self._revoke_sessions(user.id, except_id=session.id)
        self.audit.record(
            self.db, AuditAction.PASSWORD_CHANGED, actor_user_id=user.id, meta=self.meta
        )

    def update_profile(self, user: User, *, display_name: str) -> User:
        user.display_name = display_name
        self.audit.record(
            self.db, AuditAction.PROFILE_UPDATED, actor_user_id=user.id, meta=self.meta
        )
        return user
