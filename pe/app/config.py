"""Runtime configuration for the PE Compass backend, read from the environment.

Every value has a dev-friendly default so the service boots out of the box, but
secrets (JWT signing key, push credentials, the internal push-admin key) MUST be
overridden in any real deployment.
"""

import os
from datetime import timedelta

# --- JWT / auth ---------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me-please-use-a-long-random-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "30")))
REFRESH_TOKEN_TTL = timedelta(days=int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30")))

# --- Password-reset OTP -------------------------------------------------------
# Forgot-password emails a short-lived numeric code (OTP) rather than a link.
OTP_LENGTH = int(os.getenv("PASSWORD_RESET_OTP_LENGTH", "6"))
OTP_TTL = timedelta(minutes=int(os.getenv("PASSWORD_RESET_OTP_TTL_MINUTES", "10")))
# Wrong guesses allowed before a code is burned.
OTP_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_OTP_MAX_ATTEMPTS", "5"))

# --- Email / SMTP (password-reset delivery) -----------------------------------
# Leave SMTP_HOST empty for dev: the reset code is logged instead of emailed.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@pecompass.local")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

# --- Push notifications -------------------------------------------------------
# Legacy FCM server key (Authorization: key=...). When empty, the sender runs in
# stub mode: it resolves device tokens and logs, but delivers nothing.
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
# Shared secret that gates the server-to-server /notifications/send endpoint.
PUSH_ADMIN_KEY = os.getenv("PUSH_ADMIN_KEY", "")

# --- Admin panel (/pe/admin) --------------------------------------------------
# The SQLAdmin UI is gated by an email allowlist (ADMIN_EMAILS + ADMIN_EMAIL)
# whose members log in with their normal account password. ADMIN_SECRET_KEY
# signs the admin session cookie — CHANGE it in production.
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "dev-only-change-me")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
