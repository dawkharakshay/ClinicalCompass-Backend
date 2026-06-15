"""Authentication routes: register, login, logout, current user."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.enums import UserRole
from app.models import PasswordResetToken, Token, User
from app.oauth import OAuthError, OAuthIdentity, verify_apple, verify_google
from app.schemas import (
    AppleOAuthRequest,
    ErrorResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleOAuthRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenOut,
    UserCreate,
    UsernameAvailableResponse,
    UsernameGenerateRequest,
    UsernameGenerateResponse,
    UserOut,
)
from app.email import send_password_reset_otp
from app.security import (
    OTP_MAX_ATTEMPTS,
    OTP_TTL,
    generate_otp,
    generate_token,
    hash_otp,
    hash_password,
    otp_expiry,
    token_expiry,
    verify_otp,
    verify_password,
)
from app.usernames import find_available_username, slugify_full_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=True)


@router.get(
    "/username",
    response_model=UsernameAvailableResponse,
    summary="Check whether a username is available",
    description="Returns whether the given username is free. Use this to "
    "validate the username a user typed before registering.",
)
def username_available(
    username: str = Query(..., min_length=1, examples=["jane.smith"]),
    db: Session = Depends(get_db),
) -> UsernameAvailableResponse:
    existing = db.scalar(select(User).where(User.username == username))
    return UsernameAvailableResponse(username=username, available=existing is None)


@router.post(
    "/username",
    response_model=UsernameGenerateResponse,
    summary="Generate an available username from a full name",
    description="Derives a username from the given full name (e.g. "
    "'Dr. Jane Smith' -> 'jane.smith'), checks it against existing users, and "
    "returns a free username plus a few alternatives. Creates nothing.",
)
def generate_username(
    payload: UsernameGenerateRequest, db: Session = Depends(get_db)
) -> UsernameGenerateResponse:
    base = slugify_full_name(payload.full_name)
    username, alternatives = find_available_username(db, base)
    return UsernameGenerateResponse(
        full_name=payload.full_name,
        username=username,
        alternatives=alternatives,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a user account from full name, email, password and "
    "role. A username may be supplied; if omitted it is generated from the "
    "full name (e.g. 'Dr. Jane Smith' -> 'jane.smith', with a numeric suffix "
    "on collision). The password is hashed with bcrypt before storage. "
    "Username and email must each be unique.",
    responses={
        409: {"model": ErrorResponse, "description": "Username or email already taken"},
    },
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if payload.username:
        if db.scalar(select(User).where(User.username == payload.username)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        username = payload.username
    else:
        # No username supplied: derive an available one from the full name.
        username, _ = find_available_username(db, slugify_full_name(payload.full_name))

    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        username=username,
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Log in and obtain an access token",
    description="Validates the email and password and returns an opaque "
    "bearer token (no JWT) that expires after 24 hours.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid email or password"},
        403: {"model": ErrorResponse, "description": "User account is disabled"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email))

    # Verify even on missing user to reduce account-enumeration timing leaks.
    valid = user is not None and verify_password(payload.password, user.hashed_password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    token = Token(
        token=generate_token(),
        user_id=user.id,
        expires_at=token_expiry(),
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return TokenOut(access_token=token.token, expires_at=token.expires_at)


def _issue_token(user: User, db: Session) -> TokenOut:
    """Mint and persist an opaque access token for ``user``."""
    token = Token(token=generate_token(), user=user, expires_at=token_expiry())
    db.add(token)
    db.commit()
    db.refresh(token)
    return TokenOut(access_token=token.token, expires_at=token.expires_at)


def _login_with_identity(
    identity: OAuthIdentity, role: UserRole | None, db: Session
) -> TokenOut:
    """Resolve a verified provider identity to a user and issue a token.

    Find-or-create-or-link:
      1. An existing account already bound to this (provider, subject).
      2. Else, if the provider asserts a *verified* email matching an existing
         account, link this identity onto it (auto-link by verified email).
      3. Else, create a new account — ``role`` is required for this case only.
    """
    user = db.scalar(
        select(User).where(
            User.oauth_provider == identity.provider,
            User.oauth_subject == identity.subject,
        )
    )

    # Auto-link onto an existing account, but only on a verified email — an
    # unverified email must never be allowed to claim another user's account.
    if user is None and identity.email and identity.email_verified:
        user = db.scalar(select(User).where(User.email == identity.email))
        if user is not None:
            user.oauth_provider = identity.provider
            user.oauth_subject = identity.subject

    if user is None:
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="role is required to create a new account",
            )

        # Don't claim an email another account owns (only reachable when the
        # provider did not verify it); leave the new account email-less instead.
        email = identity.email
        if email is not None and db.scalar(select(User).where(User.email == email)):
            email = None

        seed = identity.full_name or (email.split("@")[0] if email else "user")
        username, _ = find_available_username(db, slugify_full_name(seed))
        user = User(
            username=username,
            full_name=identity.full_name,
            role=role,
            email=email,
            hashed_password=None,
            oauth_provider=identity.provider,
            oauth_subject=identity.subject,
        )
        db.add(user)
        # Flush so column defaults (notably is_active) populate before we read
        # them below — on an unflushed instance is_active is still None.
        db.flush()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return _issue_token(user, db)


@router.post(
    "/oauth/google",
    response_model=TokenOut,
    summary="Log in or sign up with Google",
    description="Verifies a Google ID token (from the native Sign-In SDK) and "
    "returns an opaque bearer token. On a first sign-in a new account is created "
    "and `role` is required; if the verified Google email matches an existing "
    "account, the Google identity is linked to it.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid token or missing role"},
        403: {"model": ErrorResponse, "description": "User account is disabled"},
    },
)
def oauth_google(payload: GoogleOAuthRequest, db: Session = Depends(get_db)) -> TokenOut:
    try:
        identity = verify_google(payload.id_token)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return _login_with_identity(identity, payload.role, db)


@router.post(
    "/oauth/apple",
    response_model=TokenOut,
    summary="Log in or sign up with Apple",
    description="Verifies an Apple identity token (from Sign in with Apple) and "
    "returns an opaque bearer token. On a first sign-in a new account is created "
    "and `role` is required; `full_name` should be sent on the first "
    "authorization because Apple only returns the name once. If the verified "
    "Apple email matches an existing account, the Apple identity is linked to it.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid token or missing role"},
        403: {"model": ErrorResponse, "description": "User account is disabled"},
    },
)
def oauth_apple(payload: AppleOAuthRequest, db: Session = Depends(get_db)) -> TokenOut:
    try:
        identity = verify_apple(payload.identity_token, full_name=payload.full_name)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return _login_with_identity(identity, payload.role, db)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request a password-reset code (OTP)",
    description="Emails a short-lived, one-time numeric code (OTP) to the "
    "account with the given email. The response is identical whether or not the "
    "email is registered, to avoid account enumeration. Any previously issued "
    "codes for the account are invalidated.\n\n"
    "The code is only ever delivered by email and is never returned in the "
    "response. When no mailer is configured (local development) it is written "
    "to the server log instead.",
)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    generic = ForgotPasswordResponse(
        message="If the email is registered, a reset code has been sent."
    )

    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active:
        return generic

    # Invalidate any outstanding codes before issuing a new one.
    for old in user.reset_tokens:
        db.delete(old)

    otp = generate_otp()
    reset = PasswordResetToken(
        token=hash_otp(otp),
        user_id=user.id,
        expires_at=otp_expiry(),
    )
    db.add(reset)
    db.commit()
    db.refresh(reset)

    # Email delivery must never 500 the request: a failure here would both leak
    # which emails exist (error vs. success) and break the reset flow. Log and
    # return the same generic response regardless.
    try:
        send_password_reset_otp(user.email, otp, int(OTP_TTL.total_seconds() // 60))
    except Exception:
        logger.exception("Failed to send password-reset OTP to %s", user.email)

    # The code is only ever emailed — never returned in the response.
    generic.expires_at = reset.expires_at
    return generic


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset the password using an emailed OTP",
    description="Sets a new password given the email and the one-time code sent "
    "by /auth/forgot-password. On success the code is consumed and all of the "
    "user's existing access tokens are revoked, forcing a fresh login. The code "
    "is invalidated after too many incorrect attempts.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired code"},
    },
)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> None:
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired code",
    )

    user = db.scalar(select(User).where(User.email == payload.email))
    reset = user.reset_tokens[0] if user and user.reset_tokens else None
    if reset is None:
        raise invalid

    expires_at = reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(reset)
        db.commit()
        raise invalid

    if not verify_otp(payload.otp, reset.token):
        reset.attempts += 1
        # Burn the code once the guess budget is exhausted.
        if reset.attempts >= OTP_MAX_ATTEMPTS:
            db.delete(reset)
        db.commit()
        raise invalid

    user.hashed_password = hash_password(payload.new_password)

    # Consume the code and revoke all active sessions.
    db.delete(reset)
    for token in user.tokens:
        db.delete(token)
    db.commit()


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (revoke the current token)",
    description="Deletes the supplied bearer token from the database, "
    "immediately revoking it.",
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> None:
    token = db.scalar(select(Token).where(Token.token == credentials.credentials))
    if token is not None:
        db.delete(token)
        db.commit()


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the current authenticated user",
    description="Returns the user that owns the supplied bearer token.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "User account is disabled"},
    },
)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
