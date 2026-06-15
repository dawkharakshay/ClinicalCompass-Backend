"""One-off migration: add federated-login support to the ``users`` table.

Adds ``oauth_provider`` / ``oauth_subject`` (nullable) plus a unique constraint
on the pair, and relaxes ``hashed_password`` to be nullable so OAuth-only
accounts (which have no password) can be stored.

``Base.metadata.create_all`` only creates *missing* tables, never alters an
existing one, so a database created before this change needs this script.
Idempotent and safe to run more than once. Works on SQLite and Postgres.

Run:  python scripts/migrate_oauth_columns.py
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import engine


def _columns(conn) -> set[str]:
    return {c["name"] for c in inspect(conn).get_columns("users")}


def _migrate_postgres(conn) -> None:
    cols = _columns(conn)
    if "oauth_provider" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(16)"))
    if "oauth_subject" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN oauth_subject VARCHAR(255)"))
    conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"))
    conn.execute(
        text(
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM pg_constraint "
            "WHERE conname = 'uq_users_oauth_identity') THEN "
            "ALTER TABLE users ADD CONSTRAINT uq_users_oauth_identity "
            "UNIQUE (oauth_provider, oauth_subject); END IF; END $$;"
        )
    )


def _migrate_sqlite(conn) -> None:
    # SQLite cannot ALTER a column to drop NOT NULL, so rebuild the table.
    # ADD COLUMN is supported and lands the columns nullable by default.
    cols = _columns(conn)
    if "oauth_provider" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(16)"))
    if "oauth_subject" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN oauth_subject VARCHAR(255)"))

    notnull = {
        c["name"] for c in inspect(conn).get_columns("users") if not c["nullable"]
    }
    if "hashed_password" not in notnull:
        return  # Already nullable — nothing left to do.

    conn.execute(text("ALTER TABLE users RENAME TO users_old"))
    conn.execute(
        text(
            "CREATE TABLE users ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "username VARCHAR(50) NOT NULL, "
            "full_name VARCHAR(255), "
            "role VARCHAR(32) NOT NULL, "
            "email VARCHAR(255), "
            "hashed_password VARCHAR(255), "
            "oauth_provider VARCHAR(16), "
            "oauth_subject VARCHAR(255), "
            "is_active BOOLEAN NOT NULL, "
            "created_at DATETIME NOT NULL, "
            "CONSTRAINT uq_users_oauth_identity UNIQUE (oauth_provider, oauth_subject))"
        )
    )
    conn.execute(
        text(
            "INSERT INTO users (id, username, full_name, role, email, "
            "hashed_password, oauth_provider, oauth_subject, is_active, created_at) "
            "SELECT id, username, full_name, role, email, hashed_password, "
            "oauth_provider, oauth_subject, is_active, created_at FROM users_old"
        )
    )
    conn.execute(text("DROP TABLE users_old"))
    conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
    conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))


def main() -> None:
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            _migrate_postgres(conn)
        elif engine.dialect.name == "sqlite":
            _migrate_sqlite(conn)
        else:
            raise SystemExit(f"Unsupported database: {engine.dialect.name}")
    print("users table migrated for OAuth login.")


if __name__ == "__main__":
    main()
