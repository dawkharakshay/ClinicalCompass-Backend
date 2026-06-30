# PE Compass backend

A standalone FastAPI service — the custom backend for the **PE Compass** app,
replacing Supabase (auth + database + push). It has its own PostgreSQL database
and is served behind the existing nginx reverse proxy at **`/pe/`**. Fully
independent of the main ClinicalCompass `app/` package.

The full endpoint contract lives in [`BACKEND_API.md`](./BACKEND_API.md).

## Auth model

- **Access token** — short-lived stateless JWT (HS256), sent as
  `Authorization: Bearer <token>`. The server extracts the user id and **scopes
  every query to that user** (application-level ownership, replacing Supabase RLS).
- **Refresh token** — opaque, DB-backed, **rotated on every `/auth/refresh`** and
  revocable on logout / password change (only a SHA-256 hash is stored).

## Endpoints (mounted at app root → public base `/pe`)

| Group | Endpoints |
|---|---|
| Auth | `POST /auth/signup`, `/auth/login`, `/auth/logout`, `/auth/refresh`, `GET /auth/session`, `POST /auth/forgot-password`, `/auth/reset-password` |
| Profiles | `GET /profile`, `PATCH /profile` |
| Patient classifications | `GET` / `POST` `/patient-classifications`, `DELETE /patient-classifications/{id}` |
| ECMO assessments | `GET` / `POST` `/ecmo-assessments`, `DELETE /ecmo-assessments/{id}` |
| Device tokens | `POST` (upsert) / `DELETE` `/device-tokens` |
| Notifications | `POST /notifications/send` (admin, gated by `X-Admin-Key`) |
| Meta | `GET /health` |

> Google OAuth (`/auth/oauth/google`) is listed as optional in the spec and is
> **not** implemented. The notification sender uses FCM; with `FCM_SERVER_KEY`
> unset it runs in stub mode (resolves tokens, logs, reports `sent: 0`).

## Layout

```
pe/
├── app/
│   ├── config.py     # env-driven settings (JWT, SMTP, FCM, admin key)
│   ├── database.py   # engine/session/Base (DATABASE_URL)
│   ├── security.py   # bcrypt + JWT + opaque-token helpers
│   ├── models.py     # users, profiles, patient_classifications,
│   │                 #   ecmo_candidacy_assessments, device_tokens,
│   │                 #   refresh_tokens, password_reset_tokens
│   ├── schemas.py    # Pydantic request/response models
│   ├── deps.py       # get_current_user (Bearer access token)
│   ├── email.py      # SMTP reset-link delivery (logs in dev)
│   ├── push.py       # FCM sender (stub without FCM_SERVER_KEY)
│   ├── routers/      # auth, profile, classifications, ecmo, device_tokens, notifications
│   └── main.py       # FastAPI app (root_path = ROOT_PATH, default /pe)
├── alembic/          # migrations
├── Dockerfile
├── docker-entrypoint.sh   # alembic upgrade head → uvicorn
└── pyproject.toml
```

## How it's wired in

`docker-compose.yml` (repo root) adds `pe-db` (PostgreSQL 16, volume `pe_pgdata`)
and `pe-api` (built from `./pe`, `ROOT_PATH=/pe`). `nginx.conf` routes `/pe/` to
the `pe-api` upstream, stripping the prefix. Config defaults live in
`.env.example` under the `PE_*` keys.

## Run

```bash
docker compose up -d --build pe-db pe-api nginx
curl http://localhost/pe/health        # {"status":"ok"}   (local NGINX_PORT=80)
# Docs: http://localhost/pe/docs
```

## Local dev (without Docker)

```bash
cd pe
uv sync
export DATABASE_URL="sqlite:///./pe.db"   # or any Postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001 --root-path /pe
```
