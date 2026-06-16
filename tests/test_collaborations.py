"""POST /collaborations — public collaboration/contact request endpoint."""

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

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_create_collaboration_minimal(client):
    r = client.post("/collaborations", json={
        "name": "Dr. Jane Smith",
        "email": "jane@example.com",
        "message": "I'd like to collaborate.",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["name"] == "Dr. Jane Smith"
    assert body["email"] == "jane@example.com"
    assert body["speciality"] is None
    assert body["message"] == "I'd like to collaborate."
    assert "created_at" in body


def test_create_collaboration_with_speciality(client):
    r = client.post("/collaborations", json={
        "name": "Dr. Lee",
        "email": "lee@example.com",
        "speciality": "Radiation Oncology",
        "message": "Interested in the rectal cancer module.",
    })
    assert r.status_code == 201
    assert r.json()["speciality"] == "Radiation Oncology"


@pytest.mark.parametrize("payload, missing", [
    ({"email": "a@b.com", "message": "hi"}, "name"),
    ({"name": "A", "message": "hi"}, "email"),
    ({"name": "A", "email": "a@b.com"}, "message"),
])
def test_required_fields(client, payload, missing):
    r = client.post("/collaborations", json=payload)
    assert r.status_code == 422
    assert any(missing in err["loc"] for err in r.json()["detail"])


def test_invalid_email_rejected(client):
    r = client.post("/collaborations", json={
        "name": "A", "email": "not-an-email", "message": "hi",
    })
    assert r.status_code == 422


def test_blank_required_rejected(client):
    r = client.post("/collaborations", json={
        "name": "", "email": "a@b.com", "message": "hi",
    })
    assert r.status_code == 422
