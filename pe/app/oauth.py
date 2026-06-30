"""Verify Google / Apple OpenID Connect identity tokens.

The mobile app performs the native sign-in dance with the provider and obtains
an *identity token* (a signed JWT). The backend verifies that token's signature
against the provider's published public keys (JWKS) and validates its issuer,
audience and expiry, then trusts the claims *inside* it (subject, email, ...).
Nothing the client sends alongside the token is trusted for identity.

Ported from the main ClinicalCompass app (`app/oauth.py`).

Configuration (env):
  GOOGLE_CLIENT_IDS  comma-separated OAuth client IDs accepted as the ``aud``
                     (typically your iOS and Android client IDs).
  APPLE_CLIENT_IDS   comma-separated app/service IDs accepted as the ``aud``.
"""

import os
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

GOOGLE_ISSUERS = ["https://accounts.google.com", "accounts.google.com"]
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"

APPLE_ISSUERS = ["https://appleid.apple.com"]
APPLE_JWKS_URI = "https://appleid.apple.com/auth/keys"


class OAuthError(Exception):
    """Raised when an identity token is missing, invalid, or untrusted."""


@dataclass
class OAuthIdentity:
    """The verified identity extracted from a provider's token."""

    provider: str
    subject: str
    email: str | None
    email_verified: bool
    full_name: str | None


# One JWK client per provider, so signing keys are fetched once and cached.
_jwk_clients: dict[str, PyJWKClient] = {}


def _jwk_client(jwks_uri: str) -> PyJWKClient:
    client = _jwk_clients.get(jwks_uri)
    if client is None:
        client = PyJWKClient(jwks_uri, cache_keys=True)
        _jwk_clients[jwks_uri] = client
    return client


def _audiences(env_var: str) -> list[str]:
    raw = os.getenv(env_var, "")
    return [a.strip() for a in raw.split(",") if a.strip()]


def _decode(token: str, *, jwks_uri: str, audiences: list[str], issuers: list[str]) -> dict:
    if not audiences:
        # No configured client IDs means we cannot validate ``aud`` — refuse
        # rather than accept a token for an unknown audience.
        raise OAuthError("OAuth provider is not configured on the server")
    try:
        signing_key = _jwk_client(jwks_uri).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audiences,
            issuer=issuers,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.exceptions.PyJWKClientError as exc:
        raise OAuthError("Could not fetch provider signing keys") from exc
    except jwt.PyJWTError as exc:
        raise OAuthError("Invalid identity token") from exc


def verify_google(id_token: str) -> OAuthIdentity:
    """Verify a Google ID token and return the identity it asserts."""
    claims = _decode(
        id_token,
        jwks_uri=GOOGLE_JWKS_URI,
        audiences=_audiences("GOOGLE_CLIENT_IDS"),
        issuers=GOOGLE_ISSUERS,
    )
    return OAuthIdentity(
        provider="google",
        subject=claims["sub"],
        email=claims.get("email"),
        email_verified=bool(claims.get("email_verified", False)),
        full_name=claims.get("name"),
    )


def verify_apple(identity_token: str, full_name: str | None = None) -> OAuthIdentity:
    """Verify an Apple identity token and return the identity it asserts.

    Apple never includes the user's name in the token — it is returned only on
    the first authorization — so it must be supplied separately by the client.
    """
    claims = _decode(
        identity_token,
        jwks_uri=APPLE_JWKS_URI,
        audiences=_audiences("APPLE_CLIENT_IDS"),
        issuers=APPLE_ISSUERS,
    )
    # Apple sends email_verified as a bool or the strings "true"/"false".
    raw_verified = claims.get("email_verified", False)
    email_verified = raw_verified is True or raw_verified == "true"
    return OAuthIdentity(
        provider="apple",
        subject=claims["sub"],
        email=claims.get("email"),
        email_verified=email_verified,
        full_name=full_name,
    )
