"""Seed `specialities` and `modules` from app/seed/modules_seed.json.

Idempotent: matches specialities by title and modules by (speciality, title),
so re-running only inserts what's missing. Runs against whatever DATABASE_URL
is configured (Postgres in Docker, or SQLite locally).

    uv run python scripts/seed_modules.py
    # or against local SQLite:
    DATABASE_URL=sqlite:///./clinicalcompass.db uv run python scripts/seed_modules.py
"""

import json
from pathlib import Path

from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models import Module, Speciality

SEED_FILE = Path(__file__).resolve().parent.parent / "app" / "seed" / "modules_seed.json"


def run() -> None:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))

    # Ensure tables exist (the app also does this on startup).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    created_specs = created_mods = 0
    try:
        key_to_spec: dict[str, Speciality] = {}
        for s in data["specialities"]:
            spec = db.scalar(select(Speciality).where(Speciality.title == s["title"]))
            if spec is None:
                spec = Speciality(title=s["title"], description=s.get("description"))
                db.add(spec)
                db.flush()  # assign spec.id
                created_specs += 1
            key_to_spec[s["key"]] = spec

        for m in data["modules"]:
            spec = key_to_spec[m["speciality_key"]]
            exists = db.scalar(
                select(Module).where(
                    Module.speciality_id == spec.id, Module.title == m["title"]
                )
            )
            if exists is None:
                db.add(
                    Module(
                        speciality_id=spec.id,
                        title=m["title"],
                        description=m.get("description"),
                        form={"steps": []},
                    )
                )
                created_mods += 1

        db.commit()

        total_specs = db.scalar(select(func.count()).select_from(Speciality))
        total_mods = db.scalar(select(func.count()).select_from(Module))
        print(
            f"Seed complete. "
            f"specialities: +{created_specs} (total {total_specs}) | "
            f"modules: +{created_mods} (total {total_mods})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
