"""Auth endpoints — replaces ``supabase.auth.*``.

Access tokens are stateless JWTs; refresh tokens are opaque, DB-backed, and
rotated on every use so a stolen refresh token has a short useful life.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import security
from app.config import APP_BASE_URL
from app.database import get_db
from app.deps import get_current_user
from app.email import send_password_reset
from app.models import PasswordResetToken, Profile, RefreshToken, User
from app.oauth import OAuthError, OAuthIdentity, verify_apple, verify_google
from app.schemas import (
    AccessRefresh,
    AppleOAuthRequest,
    ForgotPasswordRequest,
    GoogleOAuthRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SessionOut,
    SignupRequest,
    TokenPair,
    UserOut,
)

logger = logging.getLogger("pe.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _aware(dt: datetime) -> datetime:
    """Treat naive datetimes (e.g. from SQLite) as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _issue_refresh_token(db: Session, user: User) -> str:
    raw = security.generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=security.refresh_token_expiry(),
        )
    )
    return raw


def _token_pair(db: Session, user: User) -> TokenPair:
    access = security.create_access_token(str(user.id))
    refresh = _issue_refresh_token(db, user)
    return TokenPair(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Create a user and auto-create their profile (old ``handle_new_user``)."""
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=email, password_hash=security.hash_password(payload.password))
    user.profile = Profile(
        display_name=payload.full_name,
        hospital_affiliation=payload.hospital_affiliation,
    )
    db.add(user)
    db.flush()  # assign user.id before issuing tokens

    pair = _token_pair(db, user)
    db.commit()
    return pair


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User account is disabled")

    pair = _token_pair(db, user)
    db.commit()
    return pair


def _login_with_identity(
    identity: OAuthIdentity, db: Session, hospital_affiliation: str | None = None
) -> TokenPair:
    """Resolve a verified provider identity to a user and issue a token pair.

    Find-or-create-or-link:
      1. An account already bound to this (provider, subject).
      2. Else, if the provider asserts a *verified* email matching an existing
         account, link this identity onto it (auto-link by verified email).
      3. Else, create a new account + profile.
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
        existing = db.scalar(select(User).where(User.email == identity.email.lower()))
        if existing is not None:
            existing.oauth_provider = identity.provider
            existing.oauth_subject = identity.subject
            user = existing

    if user is None:
        # PE accounts require an email (NOT NULL). Providers supply one in
        # practice (Google always; Apple via the private-relay address).
        if not identity.email:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Provider did not supply an email address"
            )
        email = identity.email.lower()
        # Email is taken but we couldn't auto-link (provider didn't verify it):
        # refuse rather than hijack or duplicate.
        if db.scalar(select(User).where(User.email == email)):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "An account with this email already exists"
            )
        user = User(
            email=email,
            password_hash=None,
            oauth_provider=identity.provider,
            oauth_subject=identity.subject,
        )
        user.profile = Profile(
            display_name=identity.full_name, hospital_affiliation=hospital_affiliation
        )
        db.add(user)
        db.flush()

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User account is disabled")

    pair = _token_pair(db, user)
    db.commit()
    return pair


@router.post("/oauth/google", response_model=TokenPair, summary="Log in or sign up with Google")
def oauth_google(payload: GoogleOAuthRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Verify a Google ID token (native Sign-In SDK) and return a token pair.

    Creates the account + profile on first sign-in; if the verified Google email
    matches an existing account, the Google identity is linked to it.
    """
    try:
        identity = verify_google(payload.id_token)
    except OAuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _login_with_identity(identity, db, payload.hospital_affiliation)


@router.post("/oauth/apple", response_model=TokenPair, summary="Log in or sign up with Apple")
def oauth_apple(payload: AppleOAuthRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Verify an Apple identity token (Sign in with Apple) and return a token pair.

    Send ``full_name`` on the first authorization — Apple only returns the name
    once. If the verified Apple email matches an existing account, the Apple
    identity is linked to it.
    """
    try:
        identity = verify_apple(payload.identity_token, full_name=payload.full_name)
    except OAuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _login_with_identity(identity, db, payload.hospital_affiliation)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Revoke all of the user's refresh tokens (sign out)."""
    for rt in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)
        )
    ):
        rt.revoked = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/refresh", response_model=AccessRefresh)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessRefresh:
    """Rotate a refresh token, returning a fresh access + refresh pair."""
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == security.hash_token(payload.refresh_token)
        )
    )
    if token is None or token.revoked or _aware(token.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    token.revoked = True  # rotate
    new_refresh = _issue_refresh_token(db, user)
    access = security.create_access_token(str(user.id))
    db.commit()
    return AccessRefresh(access_token=access, refresh_token=new_refresh)


@router.get("/session", response_model=SessionOut)
def session(user: User = Depends(get_current_user)) -> SessionOut:
    """Replaces ``getSession()`` / ``getUser()``."""
    return SessionOut(user=UserOut.model_validate(user))


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Permanently delete the caller's account and all associated data.

    Irreversible. Cascades (``ON DELETE CASCADE``) to the profile, refresh and
    password-reset tokens, device tokens, saved classifications/assessments, and
    feedback. The access token stops working immediately (the user no longer
    exists) and every refresh token is removed, so all sessions are ended.
    """
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """Always returns 200 — never reveal whether an email is registered."""
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is not None:
        raw = security.generate_opaque_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=security.hash_token(raw),
                expires_at=security.reset_token_expiry(),
            )
        )
        db.commit()
        reset_url = f"{APP_BASE_URL}/reset-password?token={raw}"
        send_password_reset(user.email, reset_url)
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == security.hash_token(payload.token)
        )
    )
    if (
        token is None
        or token.used
        or _aware(token.expires_at) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")

    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reset token")

    user.password_hash = security.hash_password(payload.password)
    token.used = True
    # Revoke existing sessions after a password change.
    for rt in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)
        )
    ):
        rt.revoked = True
    db.commit()
    return {"message": "Password updated."}
