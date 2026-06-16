"""POST /appeal-letter-ratings — public appeal-letter rating endpoint."""

import os
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{path}")
    from fastapi.testclient import TestClient

    from app.database import Base, engine
    from app.main import app

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_create_rating_full(client):
    r = client.post("/appeal-letter-ratings", json={
        "letter_quality": 4,
        "effectiveness": 5,
        "appeal_outcome": "approved",
        "comments": "Clear and well structured.",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["letter_quality"] == 4
    assert body["effectiveness"] == 5
    assert body["appeal_outcome"] == "approved"
    assert body["comments"] == "Clear and well structured."
    assert "created_at" in body


def test_create_rating_minimal_optionals_omitted(client):
    r = client.post("/appeal-letter-ratings", json={
        "letter_quality": 3, "effectiveness": 2,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["appeal_outcome"] is None
    assert body["comments"] is None


@pytest.mark.parametrize("payload, missing", [
    ({"effectiveness": 3}, "letter_quality"),
    ({"letter_quality": 3}, "effectiveness"),
])
def test_required_ratings(client, payload, missing):
    r = client.post("/appeal-letter-ratings", json=payload)
    assert r.status_code == 422
    assert any(missing in err["loc"] for err in r.json()["detail"])


@pytest.mark.parametrize("value", [0, 6, -1])
def test_rating_out_of_range_rejected(client, value):
    r = client.post("/appeal-letter-ratings", json={
        "letter_quality": value, "effectiveness": 3,
    })
    assert r.status_code == 422


def test_non_integer_rating_rejected(client):
    r = client.post("/appeal-letter-ratings", json={
        "letter_quality": "great", "effectiveness": 3,
    })
    assert r.status_code == 422
