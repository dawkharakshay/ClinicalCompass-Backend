"""Load result-generation reference data (forms/recommendations/*.json) into
Module.recommendation.

Each file is {"title": <module title>, "recommendation": {<reference content>}}.
Matches the module by title and sets its `recommendation` column. Idempotent;
no-op for titles not present in the DB (reported). Files whose name starts with
"_" (e.g. _recommendations_report.json) are skipped.

    uv run python scripts/seed_recommendations.py
    # or against local SQLite:
    DATABASE_URL=sqlite:///./clinicalcompass.db uv run python scripts/seed_recommendations.py
"""

import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module

GEN_DIR = Path(__file__).resolve().parent.parent / "forms" / "recommendations"


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
            rec = payload.get("recommendation")
            if not title or not isinstance(rec, dict):
                print(f"  ! {f.name}: missing title/recommendation — skipped")
                skipped += 1
                continue

            mod = db.scalar(select(Module).where(Module.title == title))
            if mod is None:
                unmatched += 1
                missing.append(title)
                continue

            if mod.recommendation == rec:  # JSON round-trips to a dict; stay idempotent
                continue
            mod.recommendation = rec
            updated += 1
        db.commit()
        print(
            f"[seed_recommendations] files: {len(files)} | updated: {updated} | "
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
