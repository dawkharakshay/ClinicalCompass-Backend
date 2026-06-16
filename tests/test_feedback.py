"""POST /feedback — public feedback submission endpoint."""

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


def test_create_feedback(client):
    r = client.post("/feedback", json={
        "category": "Bug report",
        "subject": "Score bar not showing",
        "message": "The organ score bar doesn't render on the rectal module.",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["category"] == "Bug report"
    assert body["subject"] == "Score bar not showing"
    assert body["message"].startswith("The organ score bar")
    assert "created_at" in body


@pytest.mark.parametrize("payload, missing", [
    ({"subject": "s", "message": "m"}, "category"),
    ({"category": "c", "message": "m"}, "subject"),
    ({"category": "c", "subject": "s"}, "message"),
])
def test_required_fields(client, payload, missing):
    r = client.post("/feedback", json=payload)
    assert r.status_code == 422
    assert any(missing in err["loc"] for err in r.json()["detail"])


@pytest.mark.parametrize("field", ["category", "subject", "message"])
def test_blank_rejected(client, field):
    payload = {"category": "c", "subject": "s", "message": "m"}
    payload[field] = ""
    r = client.post("/feedback", json=payload)
    assert r.status_code == 422
