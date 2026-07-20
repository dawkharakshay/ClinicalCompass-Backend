"""Minimal SMTP email delivery for password-reset codes.

In dev (no ``SMTP_HOST``) the message is logged instead of sent, so the reset
flow is exercisable without an SMTP server.
"""

import logging
import smtplib
from email.message import EmailMessage

from app import config

logger = logging.getLogger("pe.email")


def send_email(to: str, subject: str, body: str) -> None:
    if not config.SMTP_HOST:
        logger.info("[email:dev] to=%s subject=%s\n%s", to, subject, body)
        return

    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    if config.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
    try:
        if config.SMTP_STARTTLS and not config.SMTP_USE_SSL:
            server.starttls()
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
    finally:
        server.quit()


def send_password_reset_otp(to: str, otp: str, ttl_minutes: int) -> None:
    send_email(
        to,
        "Your PE Compass password reset code",
        "We received a request to reset your PE Compass password.\n\n"
        f"Your password reset code is: {otp}\n\n"
        f"It expires in {ttl_minutes} minutes. If you didn't request this, you "
        "can safely ignore this email.",
    )
