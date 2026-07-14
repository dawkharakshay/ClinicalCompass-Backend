"""Registration v2: two-step, email-OTP-verified sign-up.

A new sign-up flow that proves the user owns the email before the account is
created, without touching the legacy one-shot ``POST /auth/register``:

1. ``POST /auth/v2/register`` — validate the submitted data, email a one-time
   code (OTP), and store a hashed copy of it in ``pending_registrations``.
2. ``POST /auth/v2/register/verify`` — the client re-sends the same payload plus
   the code; the code is verified and the real ``User`` is created.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import email as email_module
from app.database import get_db
from app.email import send_registration_otp
from app.models import PendingRegistration, User
from app.schemas import (
    ErrorResponse,
    RegisterOtpResponse,
    RegisterVerifyRequest,
    UserCreate,
    UserOut,
)
from app.security import (
    OTP_MAX_ATTEMPTS,
    OTP_TTL,
    generate_otp,
    hash_otp,
    hash_password,
    otp_expiry,
    verify_otp,
)
from app.usernames import find_available_username, slugify_full_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/v2", tags=["auth"])


def _resolve_username(payload: UserCreate, db: Session) -> str:
    """Validate the requested username (or derive one) — raises 409 if taken."""
    if payload.username:
        if db.scalar(select(User).where(User.username == payload.username)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        return payload.username
    # No username supplied: derive an available one from the full name.
    username, _ = find_available_username(db, slugify_full_name(payload.full_name))
    return username


def _guard_email_available(email: str, db: Session) -> None:
    """Raise 409 if an account already owns ``email``."""
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.post(
    "/register",
    response_model=RegisterOtpResponse,
    status_code=status.HTTP_200_OK,
    summary="Step 1 — verify data and email a registration code",
    description="Validates the registration data (username and email must be "
    "free) and emails a short-lived one-time code (OTP) to the given email. "
    "No account is created yet: the code is stored server-side (hashed) and must "
    "be echoed back to POST /auth/v2/register/verify along with the same data to "
    "complete sign-up. Any previously requested code for the email is replaced.\n\n"
    "When no mailer is configured (local development) the code is also written to "
    "the server log and returned in the `dev_otp` field.",
    responses={
        409: {"model": ErrorResponse, "description": "Username or email already taken"},
    },
)
def request_registration_otp(
    payload: UserCreate, db: Session = Depends(get_db)
) -> RegisterOtpResponse:
    # Validate up front so the user gets immediate feedback rather than
    # discovering a taken username/email only after entering the code.
    _resolve_username(payload, db)
    _guard_email_available(payload.email, db)

    # Replace any outstanding pending registration for this email.
    existing = db.scalar(
        select(PendingRegistration).where(PendingRegistration.email == payload.email)
    )
    if existing is not None:
        db.delete(existing)
        db.flush()

    otp = generate_otp()
    pending = PendingRegistration(
        email=payload.email,
        token=hash_otp(otp),
        expires_at=otp_expiry(),
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    ttl_minutes = int(OTP_TTL.total_seconds() // 60)
    try:
        send_registration_otp(payload.email, otp, ttl_minutes)
    except Exception:
        # Don't 500 the request on a mail failure — the user can retry step 1.
        logger.exception("Failed to send registration OTP to %s", payload.email)

    return RegisterOtpResponse(
        message="A verification code has been sent to your email.",
        email=payload.email,
        expires_at=pending.expires_at,
        # Only ever exposed when there is no real mailer (local development).
        dev_otp=None if email_module.is_configured() else otp,
    )


@router.post(
    "/register/verify",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Step 2 — verify the code and create the account",
    description="Completes registration v2. Re-send the same registration "
    "payload from step 1 together with the emailed code (`otp`). The code is "
    "checked against the pending registration for the email; on success the "
    "user account is created and the code is consumed. The code is invalidated "
    "after too many incorrect attempts or once it expires.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired code"},
        409: {"model": ErrorResponse, "description": "Username or email already taken"},
    },
)
def verify_registration(
    payload: RegisterVerifyRequest, db: Session = Depends(get_db)
) -> User:
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired code",
    )

    pending = db.scalar(
        select(PendingRegistration).where(PendingRegistration.email == payload.email)
    )
    if pending is None:
        raise invalid

    expires_at = pending.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(pending)
        db.commit()
        raise invalid

    if not verify_otp(payload.otp, pending.token):
        pending.attempts += 1
        # Burn the code once the guess budget is exhausted.
        if pending.attempts >= OTP_MAX_ATTEMPTS:
            db.delete(pending)
        db.commit()
        raise invalid

    # Re-validate uniqueness at creation time: the window between step 1 and
    # step 2 may have let another account claim the username or email.
    username = _resolve_username(payload, db)
    _guard_email_available(payload.email, db)

    user = User(
        username=username,
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    # Consume the verified code in the same transaction as the account creation.
    db.delete(pending)
    db.commit()
    db.refresh(user)
    return user
