"""Registration v2 — two-step, email-OTP-verified sign-up."""

import os
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{path}")
    # Import after DATABASE_URL is set so the engine binds to the temp DB.
    from fastapi.testclient import TestClient

    from app.database import Base, engine
    from app.main import app

    # Force the mailer into dev mode regardless of any .env SMTP_HOST: no real
    # network send, and the OTP is returned in `dev_otp` so tests can read it.
    monkeypatch.setattr("app.email.is_configured", lambda: False)

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


# The repo's test fixtures share a single engine across a run (it binds to the
# first-imported DATABASE_URL), so each test uses a distinct email to avoid
# colliding on the users.email / pending_registrations.email unique constraints.
def _payload(email):
    return {
        "full_name": "Dr. Jane Smith",
        "email": email,
        "password": "s3cret-pass",
        "role": "licensed_professional",
    }


def _request_otp(client, payload):
    return client.post("/auth/v2/register", json=payload)


def test_full_happy_path(client):
    p = _payload("happy@example.com")
    # Step 1: request the code.
    r = _request_otp(client, p)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == p["email"]
    otp = body["dev_otp"]
    assert otp and len(otp) == 6
    # No user exists yet.
    assert client.post("/auth/login", json={
        "email": p["email"], "password": p["password"],
    }).status_code == 401

    # Step 2: verify with the code + same data.
    r = client.post("/auth/v2/register/verify", json={**p, "otp": otp})
    assert r.status_code == 201
    user = r.json()
    assert user["email"] == p["email"]
    assert user["role"] == "licensed_professional"

    # The new account can log in.
    assert client.post("/auth/login", json={
        "email": p["email"], "password": p["password"],
    }).status_code == 200


def test_wrong_otp_rejected(client):
    p = _payload("wrong@example.com")
    _request_otp(client, p)
    r = client.post("/auth/v2/register/verify", json={**p, "otp": "000000"})
    assert r.status_code == 400


def test_otp_burned_after_max_attempts(client):
    p = _payload("burned@example.com")
    otp = _request_otp(client, p).json()["dev_otp"]
    wrong = "111111" if otp != "111111" else "222222"
    for _ in range(5):
        assert client.post(
            "/auth/v2/register/verify", json={**p, "otp": wrong}
        ).status_code == 400
    # Even the correct code no longer works once the budget is exhausted.
    r = client.post("/auth/v2/register/verify", json={**p, "otp": otp})
    assert r.status_code == 400


def test_verify_without_request_rejected(client):
    p = _payload("norequest@example.com")
    r = client.post("/auth/v2/register/verify", json={**p, "otp": "123456"})
    assert r.status_code == 400


def test_email_already_registered_at_step1(client):
    p = _payload("dup@example.com")
    # Create the account via the happy path first.
    otp = _request_otp(client, p).json()["dev_otp"]
    assert client.post(
        "/auth/v2/register/verify", json={**p, "otp": otp}
    ).status_code == 201
    # A second step-1 request for the same email is rejected.
    assert _request_otp(client, p).status_code == 409


def test_rerequest_replaces_previous_code(client):
    p = _payload("rerequest@example.com")
    first = _request_otp(client, p).json()["dev_otp"]
    second = _request_otp(client, p).json()["dev_otp"]
    # The first code is now stale; only the latest works.
    assert client.post(
        "/auth/v2/register/verify", json={**p, "otp": first}
    ).status_code == 400
    assert client.post(
        "/auth/v2/register/verify", json={**p, "otp": second}
    ).status_code == 201


def test_legacy_register_still_works(client):
    # The original one-shot endpoint is untouched.
    r = client.post("/auth/register", json=_payload("legacy@example.com"))
    assert r.status_code == 201
