"""Tests for the community forum — posts, comments/replies, and Yes/No polls."""

from sqlalchemy import func, select

from app.models import CommunityComment, CommunityPollVote, CommunityPost


def _signup(client, email="dr@hospital.org", password="supersecret"):
    resp = client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _user(client, email):
    return _auth(_signup(client, email=email))


# --- posts --------------------------------------------------------------------
def test_create_and_list_posts_paginated(client):
    h = _user(client, "a@x.com")
    for i in range(3):
        r = client.post(
            "/community/posts",
            json={"title": f"Q{i}", "type": "question", "body": f"body {i}"},
            headers=h,
        )
        assert r.status_code == 201, r.text

    r = client.get("/community/posts?limit=2&offset=0", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["limit"] == 2 and data["offset"] == 0
    assert len(data["items"]) == 2
    # newest first
    assert data["items"][0]["title"] == "Q2"
    assert data["items"][0]["author_name"] == "Jane Doe"
    # second page
    r2 = client.get("/community/posts?limit=2&offset=2", headers=h)
    assert len(r2.json()["items"]) == 1


def test_create_post_requires_auth(client):
    assert client.post("/community/posts", json={"body": "x"}).status_code == 401


def test_delete_own_post_but_not_others(client):
    author = _user(client, "author@x.com")
    other = _user(client, "other@x.com")
    pid = client.post("/community/posts", json={"body": "mine"}, headers=author).json()["id"]

    # a different user cannot delete it
    assert client.delete(f"/community/posts/{pid}", headers=other).status_code == 403
    # the author can
    assert client.delete(f"/community/posts/{pid}", headers=author).status_code == 204
    # gone
    assert client.delete(f"/community/posts/{pid}", headers=author).status_code == 404


def test_delete_post_cascades_comments_and_votes(client, db):
    author = _user(client, "author@x.com")
    voter = _user(client, "voter@x.com")
    pid = client.post(
        "/community/posts", json={"body": "poll it", "poll_question": "Agree?"}, headers=author
    ).json()["id"]
    client.post(f"/community/posts/{pid}/comments", json={"body": "hi"}, headers=voter)
    client.post(f"/community/posts/{pid}/poll/vote", json={"vote": True}, headers=voter)
    assert db.scalar(select(func.count()).select_from(CommunityComment)) == 1
    assert db.scalar(select(func.count()).select_from(CommunityPollVote)) == 1

    assert client.delete(f"/community/posts/{pid}", headers=author).status_code == 204
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(CommunityPost)) == 0
    assert db.scalar(select(func.count()).select_from(CommunityComment)) == 0
    assert db.scalar(select(func.count()).select_from(CommunityPollVote)) == 0


# --- comments / replies -------------------------------------------------------
def test_comment_reply_and_list_paginated(client):
    author = _user(client, "author@x.com")
    commenter = _user(client, "commenter@x.com")
    pid = client.post("/community/posts", json={"body": "discuss"}, headers=author).json()["id"]

    c1 = client.post(f"/community/posts/{pid}/comments", json={"body": "top"}, headers=commenter)
    assert c1.status_code == 201
    cid = c1.json()["id"]
    assert c1.json()["parent_comment_id"] is None

    reply = client.post(
        f"/community/posts/{pid}/comments",
        json={"body": "a reply", "parent_comment_id": cid},
        headers=author,
    )
    assert reply.status_code == 201
    assert reply.json()["parent_comment_id"] == cid

    r = client.get(f"/community/posts/{pid}/comments?limit=10&offset=0", headers=author)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert [c["body"] for c in data["items"]] == ["top", "a reply"]  # oldest first

    # comment_count is reflected on the post
    post = client.get("/community/posts", headers=author).json()["items"][0]
    assert post["comment_count"] == 2


def test_reply_parent_must_belong_to_post(client):
    h = _user(client, "a@x.com")
    p1 = client.post("/community/posts", json={"body": "p1"}, headers=h).json()["id"]
    p2 = client.post("/community/posts", json={"body": "p2"}, headers=h).json()["id"]
    c_on_p1 = client.post(f"/community/posts/{p1}/comments", json={"body": "c"}, headers=h).json()["id"]
    # replying on p2 with a parent from p1 is rejected
    r = client.post(
        f"/community/posts/{p2}/comments",
        json={"body": "bad", "parent_comment_id": c_on_p1},
        headers=h,
    )
    assert r.status_code == 400


def test_delete_own_comment_but_not_others(client):
    author = _user(client, "author@x.com")
    other = _user(client, "other@x.com")
    pid = client.post("/community/posts", json={"body": "p"}, headers=author).json()["id"]
    cid = client.post(f"/community/posts/{pid}/comments", json={"body": "c"}, headers=other).json()["id"]

    # post author cannot delete someone else's comment
    assert client.delete(f"/community/posts/{pid}/comments/{cid}", headers=author).status_code == 403
    # the comment's author can
    assert client.delete(f"/community/posts/{pid}/comments/{cid}", headers=other).status_code == 204


def test_deleting_comment_cascades_replies(client, db):
    h = _user(client, "a@x.com")
    pid = client.post("/community/posts", json={"body": "p"}, headers=h).json()["id"]
    cid = client.post(f"/community/posts/{pid}/comments", json={"body": "parent"}, headers=h).json()["id"]
    client.post(
        f"/community/posts/{pid}/comments",
        json={"body": "child", "parent_comment_id": cid},
        headers=h,
    )
    assert db.scalar(select(func.count()).select_from(CommunityComment)) == 2
    client.delete(f"/community/posts/{pid}/comments/{cid}", headers=h)
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(CommunityComment)) == 0


# --- polls --------------------------------------------------------------------
def test_poll_at_creation_vote_and_revote(client):
    author = _user(client, "author@x.com")
    u2 = _user(client, "u2@x.com")
    pid = client.post(
        "/community/posts", json={"body": "poll", "poll_question": "Agree?"}, headers=author
    ).json()
    assert pid["has_poll"] is True and pid["poll_question"] == "Agree?"
    pid = pid["id"]

    r = client.post(f"/community/posts/{pid}/poll/vote", json={"vote": True}, headers=author)
    assert r.status_code == 200
    assert r.json()["poll_yes_count"] == 1 and r.json()["my_vote"] is True

    client.post(f"/community/posts/{pid}/poll/vote", json={"vote": False}, headers=u2)
    # author changes their mind -> yes 0, no 2
    r = client.post(f"/community/posts/{pid}/poll/vote", json={"vote": False}, headers=author)
    body = r.json()
    assert body["poll_yes_count"] == 0 and body["poll_no_count"] == 2
    assert body["my_vote"] is False


def test_add_poll_to_existing_post_and_ownership(client):
    author = _user(client, "author@x.com")
    other = _user(client, "other@x.com")
    pid = client.post("/community/posts", json={"body": "no poll yet"}, headers=author).json()["id"]

    # only the owner may add a poll
    assert client.post(
        f"/community/posts/{pid}/poll", json={"poll_question": "Q?"}, headers=other
    ).status_code == 403
    r = client.post(f"/community/posts/{pid}/poll", json={"poll_question": "Q?"}, headers=author)
    assert r.status_code == 200 and r.json()["has_poll"] is True


def test_vote_on_post_without_poll_is_404(client):
    h = _user(client, "a@x.com")
    pid = client.post("/community/posts", json={"body": "plain"}, headers=h).json()["id"]
    r = client.post(f"/community/posts/{pid}/poll/vote", json={"vote": True}, headers=h)
    assert r.status_code == 404
