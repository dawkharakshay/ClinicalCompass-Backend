"""PUT /profile — authenticated update of medical speciality and institution."""

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

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


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


def test_update_profile_details(client):
    headers = _auth_headers(client)
    r = client.put("/profile", headers=headers, json={
        "medical_speciality": "Radiation Oncology",
        "current_institution": "Mayo Clinic",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["medical_speciality"] == "Radiation Oncology"
    assert body["current_institution"] == "Mayo Clinic"
    # Persisted and visible on /auth/me.
    me = client.get("/auth/me", headers=headers).json()
    assert me["medical_speciality"] == "Radiation Oncology"
    assert me["current_institution"] == "Mayo Clinic"


def test_partial_update_leaves_other_field_untouched(client):
    headers = _auth_headers(client)
    client.put("/profile", headers=headers, json={
        "medical_speciality": "Cardiology",
        "current_institution": "Cleveland Clinic",
    })
    r = client.put("/profile", headers=headers, json={"current_institution": "Johns Hopkins"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["medical_speciality"] == "Cardiology"  # omitted -> unchanged
    assert body["current_institution"] == "Johns Hopkins"


def test_explicit_null_clears_field(client):
    headers = _auth_headers(client)
    client.put("/profile", headers=headers, json={"medical_speciality": "Neurology"})
    r = client.put("/profile", headers=headers, json={"medical_speciality": None})
    assert r.status_code == 200, r.text
    assert r.json()["medical_speciality"] is None


def test_defaults_to_null_for_new_user(client):
    headers = _auth_headers(client)
    me = client.get("/auth/me", headers=headers).json()
    assert me["medical_speciality"] is None
    assert me["current_institution"] is None


def test_requires_authentication(client):
    r = client.put("/profile", json={"medical_speciality": "Oncology"})
    assert r.status_code == 401
