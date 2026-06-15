"""Contract-test the live server against docs/api/openapi.json.

For every call we assert the HTTP status is one the spec documents for that
operation, and that the response body validates against the spec's response
schema for that status code. Run against the running stack, e.g.:

    BASE_URL=http://127.0.0.1:8090 uv run python -m utils.contract_test
"""

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from jsonschema import Draft202012Validator

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8090").rstrip("/")
SPEC_PATH = Path(__file__).parent.parent / "docs/api/openapi.json"

spec = json.loads(SPEC_PATH.read_text())

passed = 0
failed = 0


def _spec_path(path: str) -> str:
    """Map a concrete request path to its templated spec path key."""
    path = path.split("?")[0]
    if path in spec["paths"]:
        return path
    req = path.strip("/").split("/")
    for tmpl in spec["paths"]:
        seg = tmpl.strip("/").split("/")
        if len(seg) == len(req) and all(
            t.startswith("{") or t == r for t, r in zip(seg, req)
        ):
            return tmpl
    raise AssertionError(f"no spec path matches {path}")


def _validate_body(method: str, path: str, status: int, body) -> None:
    """Validate `body` against the spec's response schema for this status."""
    responses = spec["paths"][_spec_path(path)][method.lower()]["responses"]
    spec_entry = responses.get(str(status))
    if spec_entry is None:
        raise AssertionError(
            f"status {status} not documented; spec lists {list(responses)}"
        )
    schema = spec_entry.get("content", {}).get("application/json", {}).get("schema")
    if schema is None:  # e.g. 204 No Content
        return
    # The schema is typically {"$ref": "#/components/schemas/X"}. Embed the
    # spec's components into the root so same-document refs resolve.
    root = dict(schema)
    root["components"] = spec["components"]
    Draft202012Validator(root).validate(body)


def call(method, path, *, expect, json_body=None, token=None, query=None, check_schema=True):
    global passed, failed
    url = f"{BASE_URL}{path}"
    if query:
        url += "?" + "&".join(f"{k}={v}" for k, v in query.items())
    data = json.dumps(json_body).encode() if json_body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read()

    body = json.loads(raw) if raw else None
    label = f"{method:4} {path} -> {status}"
    try:
        assert status == expect, f"expected HTTP {expect}, got {status}"
        if check_schema:
            _validate_body(method, path, status, body)
        print(f"  PASS  {label}")
        passed += 1
    except AssertionError as err:
        print(f"  FAIL  {label}: {err}")
        failed += 1
    return body


def main():
    uniq = uuid.uuid4().hex[:8]
    full_name = f"Dr. Test {uniq}"
    email = f"test_{uniq}@example.com"
    password = "s3cret-pass"

    print(f"Contract testing {BASE_URL} against {SPEC_PATH.name}\n")

    # meta
    call("GET", "/health", expect=200)

    # username: GET availability + POST generate
    call("GET", "/auth/username", expect=200, query={"username": f"u{uniq}"})
    call("GET", "/auth/username", expect=422)  # missing required query param
    gen = call("POST", "/auth/username", expect=200, json_body={"full_name": full_name})
    suggested = gen["username"]

    # register (no username -> auto-generated)
    user = call(
        "POST",
        "/auth/register",
        expect=201,
        json_body={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "medical_student",
        },
    )
    username = user["username"]

    # the suggestion is now taken
    avail = call("GET", "/auth/username", expect=200, query={"username": username})
    assert avail["available"] is False, "username should be taken after register"
    assert suggested == username, "generated suggestion should match assigned username"

    # error contracts
    call(
        "POST",
        "/auth/register",
        expect=409,
        json_body={
            "full_name": "X",
            "email": email,  # duplicate
            "password": password,
            "role": "medical_student",
        },
    )
    call(
        "POST",
        "/auth/register",
        expect=422,
        json_body={  # invalid role
            "full_name": "X",
            "email": f"bad_{uniq}@example.com",
            "password": password,
            "role": "nurse",
        },
    )
    call("POST", "/auth/login", expect=401,
         json_body={"email": email, "password": "wrong"})

    # login -> token, then protected endpoints
    tok = call("POST", "/auth/login", expect=200,
               json_body={"email": email, "password": password})
    token = tok["access_token"]

    call("GET", "/auth/me", expect=200, token=token)

    # a module includes its form (stages -> fields); also a dedicated form route
    mods = call("GET", "/modules", expect=200, token=token, query={"limit": 1})
    if mods["items"]:
        mid = mods["items"][0]["id"]
        detail = call("GET", f"/modules/{mid}", expect=200, token=token)
        assert "form" in detail and "steps" in detail["form"], "module detail embeds form"
        form = call("GET", f"/modules/{mid}/form", expect=200, token=token)
        assert "steps" in form, "module form has steps"
        # auth guide: present-or-null for a real module; the detail embeds the field
        assert "auth_guide" in detail, "module detail embeds auth_guide"
        guide = call("GET", f"/modules/{mid}/auth-guide", expect=200, token=token)
        assert guide is None or isinstance(guide, dict), "auth_guide is an object or null"
    call("GET", "/modules/999999/form", expect=404, token=token)
    call("GET", "/modules/999999/auth-guide", expect=404, token=token)

    # specialities + modules: READ-ONLY via the API; managed in the admin panel.
    call("GET", "/specialities", expect=401)  # no token
    page = call("GET", "/specialities", expect=200, token=token)
    assert {"items", "next", "previous"} <= page.keys(), "paginated envelope"
    assert not ({"total", "limit", "offset"} & page.keys()), "envelope trimmed of count/limit/offset"
    assert page["previous"] is None, "no previous on first page"
    paged = call("GET", "/specialities", expect=200, token=token, query={"limit": 1, "offset": 0})
    assert len(paged["items"]) <= 1, "limit caps items"
    call("GET", "/specialities", expect=422, token=token, query={"limit": 0})  # below min
    call("GET", "/specialities", expect=422, token=token, query={"limit": 999})  # above max
    call("GET", "/specialities/999999", expect=404, token=token)
    call("GET", "/modules/999999", expect=404, token=token)

    # search/filter on specialities and modules
    nomatch = call("GET", "/specialities", expect=200, token=token,
                   query={"search_query": "zzzznomatch"})
    assert nomatch["items"] == [], "search_query with no match -> empty"
    mlist = call("GET", "/modules", expect=200, token=token)
    assert {"items", "next", "previous"} <= mlist.keys(), "modules page envelope"
    mnomatch = call("GET", "/modules", expect=200, token=token,
                    query={"search_query": "zzzznomatch"})
    assert mnomatch["items"] == [], "module search no match -> empty"
    mfilter = call("GET", "/modules", expect=200, token=token,
                   query={"specialities": 999999})
    assert mfilter["items"] == [], "module filter by missing speciality -> empty"

    # count endpoints (labeled object, auth required)
    call("GET", "/specialities/count", expect=401)  # no token
    sc = call("GET", "/specialities/count", expect=200, token=token)
    assert sc["resource"] == "specialities" and isinstance(sc["count"], int), "speciality count shape"
    mc = call("GET", "/modules/count", expect=200, token=token)
    assert mc["resource"] == "modules" and isinstance(mc["count"], int), "module count shape"

    # writes are not exposed on the API -> 405 Method Not Allowed
    call("POST", "/specialities", expect=405, token=token,
         json_body={"title": "X"}, check_schema=False)
    call("PUT", "/specialities/1", expect=405, token=token,
         json_body={"title": "X"}, check_schema=False)
    call("DELETE", "/specialities/1", expect=405, token=token, check_schema=False)
    call("POST", "/specialities/1/modules", expect=405, token=token,
         json_body={"title": "X"}, check_schema=False)
    call("PUT", "/modules/1", expect=405, token=token,
         json_body={"title": "X"}, check_schema=False)
    call("DELETE", "/modules/1", expect=405, token=token, check_schema=False)

    # logout last (revokes the token)
    call("POST", "/auth/logout", expect=204, token=token)
    call("GET", "/auth/me", expect=401, token=token)  # revoked

    print(f"\n================ {passed} passed, {failed} failed ================")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
