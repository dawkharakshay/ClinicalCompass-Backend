# ClinicalCompass API

A FastAPI application with username/password login using **opaque, server-side tokens** (no JWT). Tokens are random strings stored in the database and validated on each request.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2.0 ORM (SQLite)
- bcrypt for password hashing
- Managed with [uv](https://docs.astral.sh/uv/)

## Project layout

```
app/
  main.py          # app entry point, table creation on startup
  database.py      # engine, session, Base, get_db dependency
  models.py        # User and Token tables
  schemas.py       # Pydantic request/response models
  security.py      # password hashing + token generation
  dependencies.py  # get_current_user (Bearer token auth)
  routers/auth.py  # /auth/register, /login, /logout, /me
```

## Run with Docker (Postgres + API + nginx)

```bash
cp .env.example .env     # adjust credentials / NGINX_PORT if needed
docker compose up -d --build
```

Services:
- **db** — Postgres 16 (data persisted in the `pgdata` volume)
- **api** — the FastAPI app (not published directly; fronted by nginx)
- **nginx** — reverse proxy, published on `http://localhost:${NGINX_PORT}` (default 8080)

Then open the docs at `http://localhost:${NGINX_PORT}/docs`. Tear down with
`docker compose down` (add `-v` to also drop the database volume).

## Run locally (without Docker)

The app reads `DATABASE_URL` from the environment (or `.env`), defaulting to a
local Postgres. To use SQLite for a quick local run instead:

```bash
DATABASE_URL="sqlite:///./clinicalcompass.db" uv run uvicorn app.main:app --reload
```

Then open the interactive docs at http://127.0.0.1:8000/docs

## Endpoints

| Method | Path             | Auth         | Description                               |
|--------|------------------|--------------|-------------------------------------------|
| POST   | `/auth/register` | none         | Create a user (username, password, email) |
| POST   | `/auth/login`    | none         | Returns an opaque access token            |
| GET    | `/auth/me`       | Bearer token | Current user                              |
| POST   | `/auth/logout`   | Bearer token | Revokes (deletes) the token               |
| GET    | `/health`        | none         | Health check                              |

## Example

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"drsmith","password":"s3cret-pass","email":"drsmith@example.com"}'

# Login -> { "access_token": "...", "token_type": "bearer", "expires_at": "..." }
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"drsmith","password":"s3cret-pass"}'

# Use the token
curl http://127.0.0.1:8000/auth/me \
  -H 'Authorization: Bearer <access_token>'
```

## How auth works (no JWT)

1. On login, the server generates a random URL-safe token (`secrets.token_urlsafe`) and stores it in the `tokens` table with a 24h expiry.
2. The client sends it as `Authorization: Bearer <token>`.
3. `get_current_user` looks the token up in the DB, checks expiry, and returns the owning user. Expired tokens are deleted on access.
4. Logout deletes the token row, immediately revoking it.

Token TTL is configured in `app/security.py` (`TOKEN_TTL`).
