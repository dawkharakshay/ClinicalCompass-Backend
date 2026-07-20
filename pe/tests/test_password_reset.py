"""Tests for the OTP-based forgot/reset password flow."""

import uuid

import pytest
from sqlalchemy import func, select

from app.models import PasswordResetToken, RefreshToken, User


@pytest.fixture
def sent_otps(monkeypatch):
    """Capture OTPs the endpoint would email (they're never returned in the API)."""
    captured: dict[str, str] = {}

    def _capture(to, otp, ttl_minutes):
        captured[to] = otp

    # The router imported the name into its own module namespace.
    monkeypatch.setattr("app.routers.auth.send_password_reset_otp", _capture)
    return captured


def _signup(client, email="dr@hospital.org", password="supersecret"):
    resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_forgot_password_is_generic_for_unknown_email(client, db, sent_otps):
    resp = client.post("/auth/forgot-password", json={"email": "nobody@nowhere.org"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["expires_at"] is None
    assert "nobody@nowhere.org" not in sent_otps
    # No reset row is created for a non-existent account.
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 0


def test_forgot_password_issues_otp_for_known_email(client, db, sent_otps):
    _signup(client)
    resp = client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    assert resp.status_code == 200
    assert resp.json()["expires_at"] is not None
    # A single hashed code was stored; the OTP itself is not in the response.
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 1
    assert "dr@hospital.org" in sent_otps
    assert sent_otps["dr@hospital.org"].isdigit()


def test_reset_password_with_valid_otp(client, db, sent_otps):
    _signup(client)
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    otp = sent_otps["dr@hospital.org"]

    resp = client.post(
        "/auth/reset-password",
        json={"email": "dr@hospital.org", "otp": otp, "new_password": "brand-new-pass"},
    )
    assert resp.status_code == 200

    # Code is consumed, old password rejected, new one accepted.
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 0
    assert client.post(
        "/auth/login", json={"email": "dr@hospital.org", "password": "supersecret"}
    ).status_code == 401
    assert client.post(
        "/auth/login", json={"email": "dr@hospital.org", "password": "brand-new-pass"}
    ).status_code == 200


def test_reset_password_revokes_existing_sessions(client, db, sent_otps):
    tokens = _signup(client)
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    otp = sent_otps["dr@hospital.org"]

    client.post(
        "/auth/reset-password",
        json={"email": "dr@hospital.org", "otp": otp, "new_password": "brand-new-pass"},
    )
    # The refresh token from signup no longer works after the password change.
    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 401


def test_reset_password_rejects_wrong_otp(client, sent_otps):
    _signup(client)
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})

    resp = client.post(
        "/auth/reset-password",
        json={"email": "dr@hospital.org", "otp": "000000", "new_password": "brand-new-pass"},
    )
    assert resp.status_code == 400
    # Original password still works.
    assert client.post(
        "/auth/login", json={"email": "dr@hospital.org", "password": "supersecret"}
    ).status_code == 200


def test_otp_burned_after_max_attempts(client, db, sent_otps):
    _signup(client)
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    otp = sent_otps["dr@hospital.org"]

    # Exhaust the guess budget (OTP_MAX_ATTEMPTS = 5) with wrong codes.
    for _ in range(5):
        bad = client.post(
            "/auth/reset-password",
            json={"email": "dr@hospital.org", "otp": "111111", "new_password": "x" * 8},
        )
        assert bad.status_code == 400

    # The code is now gone, so even the *correct* OTP fails.
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 0
    resp = client.post(
        "/auth/reset-password",
        json={"email": "dr@hospital.org", "otp": otp, "new_password": "brand-new-pass"},
    )
    assert resp.status_code == 400


def test_forgot_password_replaces_previous_code(client, db, sent_otps):
    _signup(client)
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    first_otp = sent_otps["dr@hospital.org"]
    client.post("/auth/forgot-password", json={"email": "dr@hospital.org"})
    second_otp = sent_otps["dr@hospital.org"]

    # Only one outstanding code exists, and it's the latest one.
    assert db.scalar(select(func.count()).select_from(PasswordResetToken)) == 1
    stale = client.post(
        "/auth/reset-password",
        json={"email": "dr@hospital.org", "otp": first_otp, "new_password": "x" * 8},
    )
    # The old code no longer works (unless the two codes happen to collide).
    if first_otp != second_otp:
        assert stale.status_code == 400
