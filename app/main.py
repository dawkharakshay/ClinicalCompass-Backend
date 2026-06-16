"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.admin import setup_admin
from app.database import (
    Base,
    engine
)
from app.routers import (
    appeal_letter_ratings,
    auth,
    collaborations,
    denial_templates,
    feedback,
    modules,
    profile,
    specialities,
    submissions,
)
from app.storage import UPLOAD_DIR, setup_storage

# Configure local image storage before the models are used.
setup_storage()

DESCRIPTION = """
**ClinicalCompass API** — username/password authentication using opaque,
server-side tokens (no JWT).

### Auth flow
1. `POST /auth/register` to create a user.
2. `POST /auth/login` with the username + password to receive an opaque
   `access_token`.
3. Send the token as `Authorization: Bearer <access_token>` on protected
   endpoints.
4. `POST /auth/logout` to revoke the token.

Tokens are random strings stored in the database and expire after 24 hours.
"""

tags_metadata = [
    {
        "name": "auth",
        "description": "Registration, login, logout, and the current-user endpoint.",
    },
    {
        "name": "specialities",
        "description": "Read specialities and their modules.",
    },
    {
        "name": "modules",
        "description": "Read individual modules.",
    },
    {
        "name": "submissions",
        "description": "Submit a module's form and read back your submissions.",
    },
    {
        "name": "denial-templates",
        "description": "Browse/search the Denial Template Library: pre-written "
        "appeal paragraphs by denial reason and procedure.",
    },
    {
        "name": "collaborations",
        "description": "Submit collaboration / contact requests (public).",
    },
    {
        "name": "appeal-letter-ratings",
        "description": "Rate a generated appeal letter (public).",
    },
    {
        "name": "feedback",
        "description": "Submit general user feedback (public).",
    },
    {
        "name": "profile",
        "description": "Manage the authenticated user's profile, including the profile photo.",
    },
    {
        "name": "meta",
        "description": "Service health and operational endpoints.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic (`alembic upgrade head`, run from the container
    # entrypoint). This create_all is a convenience for environments that bypass
    # the entrypoint (e.g. a bare `uvicorn` in local dev or the SQLite tests): it
    # only creates missing tables and never alters existing ones, so it is a
    # no-op once migrations have run.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ClinicalCompass API",
    version="0.1.0",
    summary="Authentication API with database-backed opaque tokens.",
    description=DESCRIPTION,
    openapi_tags=tags_metadata,
    contact={"name": "ClinicalCompass", "email": "support@example.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(specialities.router)
app.include_router(modules.router)
app.include_router(submissions.router)
app.include_router(denial_templates.router)
app.include_router(collaborations.router)
app.include_router(appeal_letter_ratings.router)
app.include_router(feedback.router)
app.include_router(profile.router)

# Serve uploaded images at /uploads (proxied through nginx).
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount the Django-style admin UI at /admin.
setup_admin(app, engine)


@app.get(
    "/health",
    tags=["meta"],
    summary="Health check",
    description="Returns `{\"status\": \"ok\"}` when the service is running.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}
