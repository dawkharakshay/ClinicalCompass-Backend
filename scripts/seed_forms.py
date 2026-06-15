"""Load migrated form definitions (forms/generated/*.json) into Module.form.

Each file is {"title": <module title>, "form": {<form schema>}}. Matches the
module by title and sets its `form` column. Idempotent. No-op for titles not
present in the DB (reported).

    PYTHONPATH=/app python scripts/seed_forms.py
"""

import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module

GEN_DIR = Path(__file__).resolve().parent.parent / "forms" / "generated"


def run() -> None:
    files = sorted(GEN_DIR.glob("*.json"))
    db = SessionLocal()
    updated = skipped = unmatched = 0
    missing: list[str] = []
    try:
        for f in files:
            if f.name.startswith("_"):
                continue
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"  ! {f.name}: invalid JSON ({exc}) — skipped")
                skipped += 1
                continue

            title = payload.get("title")
            form = payload.get("form")
            if not title or not isinstance(form, dict):
                print(f"  ! {f.name}: missing title/form — skipped")
                skipped += 1
                continue

            mod = db.scalar(select(Module).where(Module.title == title))
            if mod is None:
                unmatched += 1
                missing.append(title)
                continue

            if mod.form == form:  # JSON column round-trips to a dict; compare to stay idempotent
                continue
            mod.form = form
            updated += 1
        db.commit()
        print(
            f"[seed_forms] files: {len(files)} | updated: {updated} | "
            f"unmatched: {unmatched} | skipped(bad): {skipped}"
        )
        if missing:
            print("  unmatched titles:")
            for t in missing:
                print(f"    - {t}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
