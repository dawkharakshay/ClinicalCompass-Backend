"""Load the Denial Template Library (forms/denial_templates.json) into the
denial_categories and denial_templates tables.

The JSON is {"categories": [{value,label,color}], "templates": [{id, category,
title, denialReason, applicableTo, text, references}]}. Idempotent upsert keyed
by primary key (category.value / template.id). Creates the tables if missing.

    uv run python scripts/seed_denial_templates.py
    # or against local SQLite:
    DATABASE_URL=sqlite:///./clinicalcompass.db uv run python scripts/seed_denial_templates.py
"""

import json
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import DenialCategory, DenialTemplate

SRC = Path(__file__).resolve().parent.parent / "forms" / "denial_templates.json"


def run() -> None:
    Base.metadata.create_all(bind=engine)  # create new tables if absent (no-op otherwise)
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    categories = payload.get("categories") or []
    templates = payload.get("templates") or []

    db = SessionLocal()
    cat_upserts = tpl_upserts = 0
    try:
        for pos, c in enumerate(categories):
            row = db.get(DenialCategory, c["value"])
            if row is None:
                db.add(DenialCategory(value=c["value"], label=c["label"],
                                      color=c.get("color"), position=pos))
                cat_upserts += 1
            else:
                changed = (row.label, row.color, row.position) != (c["label"], c.get("color"), pos)
                row.label, row.color, row.position = c["label"], c.get("color"), pos
                cat_upserts += int(changed)
        db.flush()  # categories must exist before templates (FK)

        for t in templates:
            fields = dict(
                category=t["category"],
                title=t["title"],
                denial_reason=t.get("denialReason"),
                text=t.get("text") or "",
                applicable_to=t.get("applicableTo") or [],
                references=t.get("references") or [],
            )
            row = db.get(DenialTemplate, t["id"])
            if row is None:
                db.add(DenialTemplate(id=t["id"], **fields))
                tpl_upserts += 1
            else:
                before = (row.category, row.title, row.denial_reason, row.text,
                          row.applicable_to, row.references)
                for k, v in fields.items():
                    setattr(row, k, v)
                after = (row.category, row.title, row.denial_reason, row.text,
                         row.applicable_to, row.references)
                tpl_upserts += int(before != after)
        db.commit()
        print(f"[seed_denial_templates] categories: {len(categories)} (upserts: {cat_upserts}) | "
              f"templates: {len(templates)} (upserts: {tpl_upserts})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
