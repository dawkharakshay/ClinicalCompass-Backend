"""Password hashing (bcrypt) and opaque token / OTP generation."""

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt

TOKEN_TTL = timedelta(hours=24)
RESET_TOKEN_TTL = timedelta(hours=1)
OTP_TTL = timedelta(minutes=10)
OTP_MAX_ATTEMPTS = 5
OTP_LENGTH = 6


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the UTF-8 digest."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str | None) -> bool:
    """Check a plaintext password against a stored bcrypt hash.

    Returns False when ``hashed`` is None — an OAuth-only account has no
    password and must never be log-in-able via the password flow.
    """
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def generate_token() -> str:
    """Generate a cryptographically random, URL-safe opaque token."""
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    """Generate a zero-padded, cryptographically random numeric OTP."""
    upper = 10**OTP_LENGTH
    return f"{secrets.randbelow(upper):0{OTP_LENGTH}d}"


def hash_otp(otp: str) -> str:
    """Hash an OTP for storage so a database leak never exposes live codes."""
    return hash_password(otp)


def verify_otp(otp: str, hashed: str) -> bool:
    """Check a plaintext OTP against its stored bcrypt hash."""
    return verify_password(otp, hashed)


def token_expiry() -> datetime:
    return datetime.now(timezone.utc) + TOKEN_TTL


def reset_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + RESET_TOKEN_TTL


def otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + OTP_TTL
