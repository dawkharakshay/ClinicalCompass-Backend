"""Password hashing (bcrypt), JWT access tokens, and opaque token helpers.

Token model:
- **Access token** — a short-lived stateless JWT (HS256) carrying the user id in
  ``sub``. Verified by signature + expiry; never stored.
- **Refresh / reset tokens** — long-lived opaque random strings. The raw value
  goes to the client; only a SHA-256 hash is stored, so a DB leak never exposes
  a usable token. Revocation is a DB row update.
"""

import hashlib
import secrets
from datetime import datetime, timezone

import jwt

from app.config import (
    ACCESS_TOKEN_TTL,
    JWT_ALGORITHM,
    JWT_SECRET,
    REFRESH_TOKEN_TTL,
    RESET_TOKEN_TTL,
)

import bcrypt


# --- Passwords ----------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the UTF-8 digest."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str | None) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# --- Access tokens (JWT) ------------------------------------------------------
def create_access_token(user_id: str) -> str:
    """Issue a signed, short-lived access JWT for ``user_id``."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TOKEN_TTL).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the ``user_id`` from a valid access token, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    sub = payload.get("sub")
    return str(sub) if sub else None


# --- Opaque tokens (refresh / reset) ------------------------------------------
def generate_opaque_token() -> str:
    """Generate a cryptographically random, URL-safe opaque token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash an opaque token for storage (SHA-256, hex)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + REFRESH_TOKEN_TTL


def reset_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + RESET_TOKEN_TTL
