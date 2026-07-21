"""Tests for discussion listing (paginated) and method-based voting.

Votes are cast by HTTP method on ``/discussions/{id}/vote``:
POST = yes, DELETE = no, PUT = flip the existing vote. No request body.
"""

import uuid

from app.models import Discussion


def _signup(client, email="dr@hospital.org", password="supersecret"):
    resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _seed(db, n=1):
    ids = []
    for i in range(n):
        d = Discussion(assessment_result=f"AR{i}", complication=f"Comp{i}")
        db.add(d)
        db.commit()
        db.refresh(d)
        ids.append(str(d.id))
    return ids


# --- pagination ---------------------------------------------------------------
def test_list_discussions_paginated(client, db):
    h = _signup(client, "a@x.com")
    _seed(db, 3)
    r = client.get("/discussions?limit=2&offset=0", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3 and data["limit"] == 2 and data["offset"] == 0
    assert len(data["items"]) == 2
    # newest first
    assert data["items"][0]["assessment_result"] == "AR2"
    assert len(client.get("/discussions?limit=2&offset=2", headers=h).json()["items"]) == 1


def test_list_requires_auth(client):
    assert client.get("/discussions").status_code == 401


# --- method-based voting ------------------------------------------------------
def test_post_casts_yes(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    r = client.post(f"/discussions/{did}/vote", headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["yes_count"] == 1 and body["no_count"] == 0 and body["my_vote"] is True


def test_delete_casts_no(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    r = client.delete(f"/discussions/{did}/vote", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["no_count"] == 1 and body["yes_count"] == 0 and body["my_vote"] is False


def test_put_flips_existing_vote(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    client.post(f"/discussions/{did}/vote", headers=h)  # yes
    r = client.put(f"/discussions/{did}/vote", headers=h)  # flip -> no
    assert r.status_code == 200
    assert r.json()["my_vote"] is False and r.json()["no_count"] == 1
    # flip again -> yes
    assert client.put(f"/discussions/{did}/vote", headers=h).json()["my_vote"] is True


def test_put_without_existing_vote_is_404(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    assert client.put(f"/discussions/{did}/vote", headers=h).status_code == 404


def test_post_then_delete_updates_same_row(client, db):
    """Voting yes then no leaves one vote (updated), not two."""
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    client.post(f"/discussions/{did}/vote", headers=h)
    body = client.delete(f"/discussions/{did}/vote", headers=h).json()
    assert body["yes_count"] == 0 and body["no_count"] == 1


def test_vote_on_missing_discussion_404(client):
    h = _signup(client, "a@x.com")
    assert client.post(f"/discussions/{uuid.uuid4()}/vote", headers=h).status_code == 404
    assert client.delete(f"/discussions/{uuid.uuid4()}/vote", headers=h).status_code == 404


# --- vote summary endpoint ----------------------------------------------------
def test_get_vote_summary(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    # before any vote
    r = client.get(f"/discussions/{did}/vote", headers=h)
    assert r.status_code == 200
    assert r.json() == {"discussion_id": did, "yes_count": 0, "no_count": 0, "my_vote": None}
    # after voting yes
    client.post(f"/discussions/{did}/vote", headers=h)
    body = client.get(f"/discussions/{did}/vote", headers=h).json()
    assert body["yes_count"] == 1 and body["no_count"] == 0 and body["my_vote"] is True


def test_get_vote_summary_missing_discussion_404(client):
    h = _signup(client, "a@x.com")
    assert client.get(f"/discussions/{uuid.uuid4()}/vote", headers=h).status_code == 404


def test_list_excludes_vote_fields(client, db):
    """The discussion list is topic-only; vote data lives on /vote now."""
    h = _signup(client, "a@x.com")
    _seed(db, 1)
    item = client.get("/discussions", headers=h).json()["items"][0]
    assert set(item.keys()) == {"id", "assessment_result", "complication", "created_at"}


def test_vote_response_is_summary_not_discussion(client, db):
    """POST/DELETE/PUT return the vote summary shape, not the discussion object."""
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    body = client.post(f"/discussions/{did}/vote", headers=h).json()
    assert set(body.keys()) == {"discussion_id", "yes_count", "no_count", "my_vote"}


# --- retract vote -------------------------------------------------------------
def test_retract_vote_clears_my_vote(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    client.post(f"/discussions/{did}/vote", headers=h)  # yes -> yes_count 1
    r = client.delete(f"/discussions/{did}/vote/me", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["my_vote"] is None and body["yes_count"] == 0 and body["no_count"] == 0


def test_retract_is_idempotent_when_not_voted(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    r = client.delete(f"/discussions/{did}/vote/me", headers=h)  # never voted
    assert r.status_code == 200 and r.json()["my_vote"] is None


def test_retract_missing_discussion_404(client):
    h = _signup(client, "a@x.com")
    assert client.delete(f"/discussions/{uuid.uuid4()}/vote/me", headers=h).status_code == 404


def test_delete_vote_still_means_no_not_retract(client, db):
    """DELETE /vote sets 'no'; DELETE /vote/me retracts — they must differ."""
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    assert client.delete(f"/discussions/{did}/vote", headers=h).json()["my_vote"] is False
    assert client.delete(f"/discussions/{did}/vote/me", headers=h).json()["my_vote"] is None


# --- create / delete discussion (any authenticated user) ----------------------
def test_create_discussion(client, db):
    h = _signup(client, "author@x.com")
    r = client.post(
        "/discussions",
        json={"assessment_result": "High risk", "complication": "Bleeding"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["assessment_result"] == "High risk" and body["complication"] == "Bleeding"
    assert set(body.keys()) == {"id", "assessment_result", "complication", "created_at"}
    # it is now listable
    assert db.get(Discussion, uuid.UUID(body["id"])) is not None


def test_create_discussion_requires_auth(client):
    assert (
        client.post(
            "/discussions",
            json={"assessment_result": "x", "complication": "y"},
        ).status_code
        == 401
    )


def test_create_discussion_rejects_blank_fields(client):
    h = _signup(client, "author@x.com")
    r = client.post(
        "/discussions",
        json={"assessment_result": "", "complication": "y"},
        headers=h,
    )
    assert r.status_code == 422


def test_delete_discussion_cascades_votes_and_comments(client, db):
    h = _signup(client, "a@x.com")
    did = _seed(db)[0]
    client.post(f"/discussions/{did}/vote", headers=h)  # a vote
    client.post(f"/discussions/{did}/comments", json={"body": "hi"}, headers=h)  # a comment
    r = client.delete(f"/discussions/{did}", headers=h)
    assert r.status_code == 204
    assert db.get(Discussion, uuid.UUID(did)) is None
    # votes + comments went with it (ON DELETE CASCADE)
    assert client.get(f"/discussions/{did}/vote", headers=h).status_code == 404


def test_delete_discussion_by_any_user(client, db):
    # a discussion is ownerless — a different user than any author may delete it
    did = _seed(db)[0]
    h = _signup(client, "someone@x.com")
    assert client.delete(f"/discussions/{did}", headers=h).status_code == 204
    assert db.get(Discussion, uuid.UUID(did)) is None


def test_delete_discussion_requires_auth(client, db):
    did = _seed(db)[0]
    assert client.delete(f"/discussions/{did}").status_code == 401


def test_delete_missing_discussion_404(client):
    h = _signup(client, "author@x.com")
    assert (
        client.delete(f"/discussions/{uuid.uuid4()}", headers=h).status_code == 404
    )
