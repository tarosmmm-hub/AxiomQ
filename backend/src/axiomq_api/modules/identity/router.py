from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Response, status

from axiomq_api.core.deps import ContainerDep, UowDep
from axiomq_api.modules.identity.cookies import (
    clear_session_cookie,
    issue_csrf_cookie,
    set_session_cookie,
)
from axiomq_api.modules.identity.deps import AuthDep, IdentityDep
from axiomq_api.modules.identity.models import User
from axiomq_api.modules.identity.schemas import (
    AcceptedOut,
    ChangePasswordRequest,
    CsrfOut,
    EmailVerifyRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(prefix="/me", tags=["me"])


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified_at is not None,
        created_at=user.created_at,
    )


@auth_router.get("/csrf", response_model=CsrfOut)
def get_csrf(response: Response, container: ContainerDep) -> CsrfOut:
    return CsrfOut(csrf_token=issue_csrf_cookie(response, container.settings))


@auth_router.post("/register", response_model=AcceptedOut, status_code=status.HTTP_202_ACCEPTED)
def register(
    body: RegisterRequest, identity: IdentityDep, uow: UowDep, background: BackgroundTasks
) -> AcceptedOut:
    identity.register(email=body.email, password=body.password, display_name=body.display_name)
    uow.commit(background)
    return AcceptedOut(
        status="accepted",
        message="Check your inbox to verify your email address, then sign in.",
    )


@auth_router.post("/login", response_model=UserOut)
def login(
    body: LoginRequest,
    identity: IdentityDep,
    uow: UowDep,
    response: Response,
    container: ContainerDep,
) -> UserOut:
    issued = identity.login(email=body.email, password=body.password)
    uow.commit()
    set_session_cookie(response, container.settings, issued.token)
    issue_csrf_cookie(response, container.settings)  # rotate CSRF token on privilege change
    auth = identity.authenticate(issued.token)
    assert auth is not None
    return user_out(auth[0])


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    auth: AuthDep,
    identity: IdentityDep,
    uow: UowDep,
    response: Response,
    container: ContainerDep,
) -> None:
    identity.logout(auth.session)
    uow.commit()
    clear_session_cookie(response, container.settings)


@auth_router.post(
    "/password-reset/request", response_model=AcceptedOut, status_code=status.HTTP_202_ACCEPTED
)
def password_reset_request(
    body: PasswordResetRequest, identity: IdentityDep, uow: UowDep, background: BackgroundTasks
) -> AcceptedOut:
    identity.request_password_reset(email=body.email)
    uow.commit(background)
    return AcceptedOut(
        status="accepted",
        message="If an account exists for that email, a reset link has been sent.",
    )


@auth_router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(
    body: PasswordResetConfirm,
    identity: IdentityDep,
    uow: UowDep,
    response: Response,
    container: ContainerDep,
) -> None:
    identity.confirm_password_reset(token=body.token, new_password=body.new_password)
    uow.commit()
    clear_session_cookie(response, container.settings)


@auth_router.post("/email/verify", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(body: EmailVerifyRequest, identity: IdentityDep, uow: UowDep) -> None:
    identity.verify_email(token=body.token)
    uow.commit()


@auth_router.post("/email/resend", status_code=status.HTTP_204_NO_CONTENT)
def resend_verification(
    auth: AuthDep, identity: IdentityDep, uow: UowDep, background: BackgroundTasks
) -> None:
    identity.resend_verification(auth.user)
    uow.commit(background)


@me_router.get("", response_model=UserOut)
def get_me(auth: AuthDep) -> UserOut:
    return user_out(auth.user)


@me_router.patch("", response_model=UserOut)
def update_me(
    body: UpdateProfileRequest, auth: AuthDep, identity: IdentityDep, uow: UowDep
) -> UserOut:
    user = identity.update_profile(auth.user, display_name=body.display_name)
    uow.commit()
    return user_out(user)


@me_router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest, auth: AuthDep, identity: IdentityDep, uow: UowDep
) -> None:
    identity.change_password(
        auth.user,
        auth.session,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    uow.commit()
