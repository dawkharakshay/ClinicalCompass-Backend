"""Tests for flat comments on discussions."""

import uuid

from sqlalchemy import func, select

from app.models import Discussion, DiscussionComment


def _signup(client, email="dr@hospital.org", password="supersecret"):
    resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _seed_discussion(db):
    d = Discussion(assessment_result="High-risk PE", complication="Major bleeding")
    db.add(d)
    db.commit()
    db.refresh(d)
    return str(d.id)


def test_add_and_list_comments_paginated(client, db):
    h = _signup(client, "a@x.com")
    did = _seed_discussion(db)
    for i in range(3):
        r = client.post(f"/discussions/{did}/comments", json={"body": f"c{i}"}, headers=h)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["author_name"] == "Jane Doe"
        assert body["discussion_id"] == did
        # nested author ref: {id, display_name, self}
        assert body["user"]["id"] == body["user_id"]
        assert body["user"]["display_name"] == "Jane Doe"
        assert body["user"]["self"] is True

    r = client.get(f"/discussions/{did}/comments?limit=2&offset=0", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3 and data["limit"] == 2 and data["offset"] == 0
    assert [c["body"] for c in data["items"]] == ["c0", "c1"]  # oldest first
    assert len(client.get(f"/discussions/{did}/comments?limit=2&offset=2", headers=h).json()["items"]) == 1


def test_list_comments_user_self_reflects_viewer(client, db):
    author = _signup(client, "author@x.com")
    did = _seed_discussion(db)
    client.post(f"/discussions/{did}/comments", json={"body": "mine"}, headers=author)

    # the author sees self=True
    mine = client.get(f"/discussions/{did}/comments", headers=author).json()["items"][0]
    assert mine["user"]["self"] is True and mine["user"]["display_name"] == "Jane Doe"

    # a different viewer sees the same author but self=False
    other = _signup(client, "other@x.com")
    theirs = client.get(f"/discussions/{did}/comments", headers=other).json()["items"][0]
    assert theirs["user"]["id"] == mine["user"]["id"]
    assert theirs["user"]["self"] is False


def test_add_comment_requires_auth(client, db):
    did = _seed_discussion(db)
    assert client.post(f"/discussions/{did}/comments", json={"body": "x"}).status_code == 401


def test_comment_on_missing_discussion_404(client):
    h = _signup(client, "a@x.com")
    r = client.post(f"/discussions/{uuid.uuid4()}/comments", json={"body": "x"}, headers=h)
    assert r.status_code == 404


def test_empty_body_rejected(client, db):
    h = _signup(client, "a@x.com")
    did = _seed_discussion(db)
    assert client.post(f"/discussions/{did}/comments", json={"body": ""}, headers=h).status_code == 422


def test_delete_own_comment_but_not_others(client, db):
    author = _signup(client, "author@x.com")
    other = _signup(client, "other@x.com")
    did = _seed_discussion(db)
    cid = client.post(f"/discussions/{did}/comments", json={"body": "mine"}, headers=author).json()["id"]

    assert client.delete(f"/discussions/{did}/comments/{cid}", headers=other).status_code == 403
    assert client.delete(f"/discussions/{did}/comments/{cid}", headers=author).status_code == 204
    assert client.delete(f"/discussions/{did}/comments/{cid}", headers=author).status_code == 404


def test_deleting_discussion_cascades_comments(client, db):
    h = _signup(client, "a@x.com")
    did = _seed_discussion(db)
    client.post(f"/discussions/{did}/comments", json={"body": "c"}, headers=h)
    assert db.scalar(select(func.count()).select_from(DiscussionComment)) == 1

    db.query(Discussion).filter(Discussion.id == uuid.UUID(did)).delete()
    db.commit()
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(DiscussionComment)) == 0
