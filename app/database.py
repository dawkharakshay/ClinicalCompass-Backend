"""Database engine, session factory, and declarative base."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load a local .env if present (no-op in containers where env is already set).
load_dotenv()

# Default to a local Postgres; override with DATABASE_URL (e.g. for SQLite or
# the Dockerised Postgres at host "db").
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://clinicalcompass:clinicalcompass@localhost:5432/clinicalcompass",
)

# check_same_thread=False is only needed for SQLite, where requests may be
# served on different threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
