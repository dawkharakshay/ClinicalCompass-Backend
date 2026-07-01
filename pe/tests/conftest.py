"""Test fixtures for the PE Compass backend.

Each test runs against a fresh, in-memory SQLite database with foreign-key
enforcement turned on, so ``ON DELETE CASCADE`` behaves like it does on the
Postgres deployment. ``get_db`` is overridden to hand endpoints a session bound
to that database, and the app's lifespan is skipped (``TestClient`` is *not*
used as a context manager) so it never touches the real Postgres engine.
"""

import os

# Point the app's module-level engine at throwaway SQLite before it is imported,
# so importing app.main never tries to reach the default Postgres URL.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db_engine():
    """A fresh in-memory SQLite DB (shared across connections) with FKs on."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection => one in-memory DB
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _record):  # noqa: ANN001
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session_factory(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture
def db(session_factory) -> Session:
    """A session for tests to inspect the database directly."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def _get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    # No context manager => the app lifespan (which create_all's the real engine)
    # does not run; the dependency override supplies the SQLite session instead.
    yield TestClient(app)
    app.dependency_overrides.clear()
