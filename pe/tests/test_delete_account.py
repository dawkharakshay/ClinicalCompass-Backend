"""Tests for ``DELETE /auth/account`` — permanent account deletion."""

import uuid

from sqlalchemy import func, select

from app.models import DeviceToken, Feedback, Profile, RefreshToken, User


def _signup(client, email="dr@hospital.org", password="supersecret"):
    resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_delete_account_returns_204(client):
    tokens = _signup(client)
    resp = client.delete("/auth/account", headers=_auth(tokens))
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_account_requires_auth(client):
    resp = client.delete("/auth/account")
    assert resp.status_code == 401  # HTTPBearer rejects the missing credential


def test_deleted_user_is_gone(client, db):
    tokens = _signup(client)
    user_id = uuid.UUID(tokens["user"]["id"])

    client.delete("/auth/account", headers=_auth(tokens))

    assert db.get(User, user_id) is None
    # The now-invalid access token no longer resolves to a user.
    assert client.get("/auth/session", headers=_auth(tokens)).status_code == 401
    # ...and the same credentials can no longer log in.
    login = client.post(
        "/auth/login", json={"email": "dr@hospital.org", "password": "supersecret"}
    )
    assert login.status_code == 401


def test_delete_cascades_to_owned_rows(client, db):
    tokens = _signup(client)
    headers = _auth(tokens)
    user_id = uuid.UUID(tokens["user"]["id"])

    # Create some data owned by the user across several tables.
    client.post("/device-tokens", json={"token": "fcm-abc", "platform": "ios"}, headers=headers)
    client.post("/feedback", json={"usefulness": "useful"}, headers=headers)
    client.patch("/profile", json={"display_name": "Jane D."}, headers=headers)

    # Sanity check the rows exist before deletion.
    assert db.scalar(select(func.count()).select_from(Profile)) == 1
    assert db.scalar(select(func.count()).select_from(DeviceToken)) == 1
    assert db.scalar(select(func.count()).select_from(Feedback)) == 1
    assert db.scalar(select(func.count()).select_from(RefreshToken)) >= 1

    resp = client.delete("/auth/account", headers=headers)
    assert resp.status_code == 204

    # Every dependent row is cascade-deleted with the user.
    db.expire_all()
    assert db.get(User, user_id) is None
    assert db.scalar(select(func.count()).select_from(Profile)) == 0
    assert db.scalar(select(func.count()).select_from(DeviceToken)) == 0
    assert db.scalar(select(func.count()).select_from(Feedback)) == 0
    assert db.scalar(select(func.count()).select_from(RefreshToken)) == 0


def test_refresh_token_rejected_after_deletion(client):
    tokens = _signup(client)
    client.delete("/auth/account", headers=_auth(tokens))

    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_email_can_be_reused_after_deletion(client):
    tokens = _signup(client)
    client.delete("/auth/account", headers=_auth(tokens))
    # A fresh signup with the same email succeeds — the account is fully gone.
    again = client.post(
        "/auth/signup",
        json={"email": "dr@hospital.org", "password": "supersecret"},
    )
    assert again.status_code == 201
