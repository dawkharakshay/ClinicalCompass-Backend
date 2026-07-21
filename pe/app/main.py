"""FastAPI application entry point for the PE Compass backend.

A custom backend that replaces Supabase (auth + database + push) for the PE
Compass app — see BACKEND_API.md for the endpoint contract. Served behind nginx
at ``/pe/``; nginx strips that prefix before proxying, and ``ROOT_PATH`` (default
``/pe``) tells FastAPI where it lives so the OpenAPI docs resolve correctly.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin import setup_admin
from app.database import Base, engine
from app.routers import (
    auth,
    community,
    device_tokens,
    discussions,
    feedback,
    profile,
)

ROOT_PATH = os.getenv("ROOT_PATH", "/pe")

DESCRIPTION = """
**PE Compass API** — custom backend (auth + database + push) replacing Supabase
for the PE Compass clinical decision-support app.

### Auth
Stateless JWT **access tokens** + opaque, rotating **refresh tokens**. Send the
access token as `Authorization: Bearer <access_token>` on protected endpoints;
the server scopes every query to the token's user (replacing Supabase RLS).
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic (`alembic upgrade head`, from the entrypoint).
    # create_all only adds missing tables, so it's a no-op after migrations —
    # a convenience for environments that bypass the entrypoint (local, tests).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PE Compass API",
    version="0.1.0",
    summary="Custom auth + data + push backend for PE Compass.",
    description=DESCRIPTION,
    root_path=ROOT_PATH,
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(device_tokens.router)
app.include_router(feedback.router)
app.include_router(discussions.router)
app.include_router(community.router)

# SQLAdmin UI at /admin (public /pe/admin behind nginx), gated by ADMIN_EMAILS.
setup_admin(app, engine)


@app.get("/health", tags=["meta"], summary="Health check")
def health() -> dict[str, str]:
    """Returns `{"status": "ok"}` when the service is running."""
    return {"status": "ok"}
