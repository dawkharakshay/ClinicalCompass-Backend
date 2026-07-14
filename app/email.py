"""Outbound email via SMTP.

Configured entirely through environment variables. When ``SMTP_HOST`` is unset
the mailer runs in *dev mode*: it logs the message instead of sending it and
``is_configured()`` reports False, which lets callers expose the OTP in the API
response for local development.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """Whether a real SMTP server is configured for outbound mail."""
    return bool(os.getenv("SMTP_HOST"))


def _send(to: str, subject: str, body: str) -> None:
    """Send a plaintext email, or log it when SMTP is not configured."""
    sender = os.getenv("SMTP_FROM", "no-reply@clinicalcompass.local")

    if not is_configured():
        logger.warning(
            "SMTP not configured; not sending email to %s. Subject=%r Body=%r",
            to,
            subject,
            body,
        )
        return

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    use_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

    if use_ssl:
        smtp: smtplib.SMTP = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context())
    else:
        smtp = smtplib.SMTP(host, port)
    try:
        if use_starttls and not use_ssl:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    finally:
        smtp.quit()


def send_password_reset_otp(to: str, otp: str, ttl_minutes: int) -> None:
    """Email a password-reset OTP to the user."""
    subject = "Your ClinicalCompass password reset code"
    body = (
        f"Your password reset code is: {otp}\n\n"
        f"It expires in {ttl_minutes} minutes. If you did not request a "
        "password reset, you can safely ignore this email.\n"
    )
    _send(to, subject, body)


def send_registration_otp(to: str, otp: str, ttl_minutes: int) -> None:
    """Email a registration verification OTP to a prospective user."""
    subject = "Your ClinicalCompass verification code"
    body = (
        f"Welcome to ClinicalCompass!\n\n"
        f"Your registration verification code is: {otp}\n\n"
        f"It expires in {ttl_minutes} minutes. If you did not try to create an "
        "account, you can safely ignore this email.\n"
    )
    _send(to, subject, body)


def _admin_recipients() -> list[str]:
    raw = os.getenv("ADMIN_EMAILS") or os.getenv("ADMIN_EMAIL") or ""
    return [a.strip() for a in raw.split(",") if a.strip()]


def send_collaboration_request(
    name: str, email: str, speciality: str | None, message: str
) -> None:
    """Notify the configured admins of a new collaboration request."""
    subject = f"New collaboration request from {name}"
    body = (
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Speciality: {speciality or '-'}\n\n"
        f"Message:\n{message}\n"
    )
    for to in _admin_recipients():
        _send(to, subject, body)
