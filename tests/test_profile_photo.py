"""PUT/DELETE /profile/photo — authenticated profile photo upload."""

import io
import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    upload_dir = tempfile.mkdtemp(prefix="uploads-")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{path}")
    from fastapi.testclient import TestClient

    from app.database import Base, engine
    from app.main import app
    from app.storage import storage

    # The storage object binds UPLOAD_DIR at import time, so repoint it at the
    # per-test directory directly (env vars are too late once imported).
    monkeypatch.setattr(storage, "_path", Path(upload_dir))

    # The engine binds DATABASE_URL at import, so the DB is shared across tests;
    # reset the schema for a clean slate (no stale avatars pointing at old dirs).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        c.upload_dir = upload_dir
        yield c


def _png_bytes(color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


def _auth_headers(client) -> dict:
    client.post("/auth/register", json={
        "full_name": "Dr. Jane Smith",
        "email": "jane@example.com",
        "password": "s3cret-pass",
        "role": "licensed_professional",
    })
    r = client.post("/auth/login", json={"email": "jane@example.com", "password": "s3cret-pass"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_upload_profile_photo(client):
    headers = _auth_headers(client)
    r = client.put(
        "/profile/photo",
        headers=headers,
        files={"file": ("avatar.png", _png_bytes(), "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["avatar_url"] is not None
    assert body["avatar_url"].startswith("/uploads/avatars/")
    assert body["avatar_url"].endswith(".png")

    # The file actually landed on disk and /auth/me reflects it.
    rel = body["avatar_url"].removeprefix("/uploads/")
    assert os.path.exists(os.path.join(client.upload_dir, rel))

    me = client.get("/auth/me", headers=headers)
    assert me.json()["avatar_url"] == body["avatar_url"]


def test_replace_photo_deletes_old_file(client):
    headers = _auth_headers(client)
    first = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("a.png", _png_bytes((255, 0, 0)), "image/png")},
    ).json()["avatar_url"]
    second = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("b.png", _png_bytes((0, 255, 0)), "image/png")},
    ).json()["avatar_url"]

    assert first != second
    old_path = os.path.join(client.upload_dir, first.removeprefix("/uploads/"))
    new_path = os.path.join(client.upload_dir, second.removeprefix("/uploads/"))
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)


def test_delete_profile_photo(client):
    headers = _auth_headers(client)
    url = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("a.png", _png_bytes(), "image/png")},
    ).json()["avatar_url"]
    path = os.path.join(client.upload_dir, url.removeprefix("/uploads/"))
    assert os.path.exists(path)

    r = client.delete("/profile/photo", headers=headers)
    assert r.status_code == 204
    assert not os.path.exists(path)
    assert client.get("/auth/me", headers=headers).json()["avatar_url"] is None


def test_delete_when_no_photo_is_noop(client):
    headers = _auth_headers(client)
    r = client.delete("/profile/photo", headers=headers)
    assert r.status_code == 204


def test_requires_authentication(client):
    r = client.put("/profile/photo", files={"file": ("a.png", _png_bytes(), "image/png")})
    assert r.status_code == 401  # HTTPBearer rejects a missing token


def test_rejects_non_image_content_type(client):
    headers = _auth_headers(client)
    r = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 415


def test_rejects_disallowed_extension(client):
    headers = _auth_headers(client)
    r = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("avatar.bmp", _png_bytes(), "image/png")},
    )
    assert r.status_code == 415


def test_rejects_corrupt_image(client):
    headers = _auth_headers(client)
    r = client.put(
        "/profile/photo", headers=headers,
        files={"file": ("avatar.png", b"not really a png", "image/png")},
    )
    assert r.status_code == 422
