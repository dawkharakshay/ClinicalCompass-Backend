"""Attach the bundled module logos (app/seed/logos/*.webp) to Module.image.

No network access: copies each bundled logo into UPLOAD_DIR (the runtime volume)
when missing, then points the matching Module at it. Modules whose logo isn't
bundled fall back to the placeholder. Idempotent — safe to run on every startup.

    PYTHONPATH=/app python scripts/seed_logos.py
"""

import json
import shutil
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module
from app.storage import UPLOAD_DIR

SEED_DIR = Path(__file__).resolve().parent.parent / "app" / "seed"
LOGO_DIR = SEED_DIR / "logos"
SEED_FILE = SEED_DIR / "modules_seed.json"
PLACEHOLDER = "placeholder-logo.webp"


def _logo_filename(logo_url: str) -> str:
    raw = logo_url.split("?", 1)[0].rsplit("/", 1)[-1]
    return Path(raw).stem + ".webp"


def run() -> None:
    modules = [m for m in json.loads(SEED_FILE.read_text(encoding="utf-8"))["modules"] if m.get("logo_url")]
    upload = Path(UPLOAD_DIR)
    upload.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    attached = 0
    try:
        for m in modules:
            filename = _logo_filename(m["logo_url"])
            src = LOGO_DIR / filename
            if not src.exists():  # logo not bundled -> placeholder
                filename = PLACEHOLDER
                src = LOGO_DIR / PLACEHOLDER
            if not src.exists():
                continue

            dest = upload / filename
            if not dest.exists():
                shutil.copyfile(src, dest)

            mod = db.scalar(select(Module).where(Module.title == m["title"]))
            if mod is None:
                continue
            # Module.image is an ImageType (storage object on read), so compare the
            # resolved filename rather than the raw attribute to stay idempotent.
            current = (getattr(mod.image, "name", None) or str(mod.image)) if mod.image else None
            if current != filename:
                mod.image = filename
                attached += 1
        db.commit()
        print(f"[seed_logos] attached/updated: {attached}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
