"""Download module logos (used by clinicalcompass.net), resize them to a small
square .webp, store them in UPLOAD_DIR, and attach each to its Module.image.

Reads logo URLs from app/seed/modules_seed.json. Handles both URL shapes the
site uses: absolute CDN URLs and relative `/manus-storage/...` paths (which
307-redirect to signed CDN URLs). Every logo is downsized to <=256x256 .webp
(originals are ~1920x1920, ~150KB+ each). Any logo that can't be fetched falls
back to a generated neutral placeholder.

Idempotent: skips a resized file that already exists; always (re)points
Module.image at the resulting filename.

    DATABASE_URL=sqlite:///./clinicalcompass.db PYTHONPATH=. .venv/bin/python scripts/fetch_logos.py
"""

import json
import os
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Module
from app.storage import UPLOAD_DIR

SEED_FILE = Path(__file__).resolve().parent.parent / "app" / "seed" / "modules_seed.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (ClinicalCompass seed)"}
SITE_ORIGIN = "https://clinicalcompass.net"  # relative /manus-storage/... paths resolve here
THUMB = (256, 256)
WEBP_QUALITY = 82
PLACEHOLDER = "placeholder-logo.webp"


def _ensure_placeholder() -> None:
    """Create a neutral placeholder logo once (for modules whose logo is missing)."""
    dest = Path(UPLOAD_DIR) / PLACEHOLDER
    if dest.exists():
        return
    img = Image.new("RGB", THUMB, "#f1f5f9")  # slate-100
    draw = ImageDraw.Draw(img)
    draw.ellipse((48, 48, 208, 208), outline="#1e293b", width=6)  # slate-800 ring
    cx, cy = 128, 128
    draw.polygon([(cx, 70), (cx + 14, cy), (cx, 186), (cx - 14, cy)], fill="#1e293b")  # N-S
    draw.polygon([(70, cy), (cx, cy - 14), (186, cy), (cx, cy + 14)], fill="#dc2626")  # E-W
    img.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)


def _resize_to_webp(raw: bytes, dest: Path) -> None:
    img = Image.open(BytesIO(raw))
    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    img.thumbnail(THUMB, Image.LANCZOS)
    img.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)


def _fetch(url: str) -> bytes:
    if url.startswith("/"):
        url = SITE_ORIGIN + url  # resolve relative path; 307 -> signed CDN URL
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted source)
        return resp.read()


def run(limit: int | None = None) -> None:
    modules = json.loads(SEED_FILE.read_text(encoding="utf-8"))["modules"]
    modules = [m for m in modules if m.get("logo_url")]
    if limit:
        modules = modules[:limit]

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    _ensure_placeholder()

    db = SessionLocal()
    downloaded = attached = fallbacks = 0
    try:
        for m in modules:
            raw_name = m["logo_url"].split("?", 1)[0].rsplit("/", 1)[-1]
            filename = Path(raw_name).stem + ".webp"  # always small webp
            dest = Path(UPLOAD_DIR) / filename

            if not (dest.exists() and dest.stat().st_size > 0):
                try:
                    _resize_to_webp(_fetch(m["logo_url"]), dest)
                    downloaded += 1
                except Exception as exc:  # noqa: BLE001
                    fallbacks += 1
                    filename = PLACEHOLDER
                    print(f"  ! {m['title']}: {exc} -> placeholder")

            mod = db.scalar(select(Module).where(Module.title == m["title"]))
            if mod is not None and mod.image != filename:
                mod.image = filename
                attached += 1
        db.commit()

        total = sum(
            f.stat().st_size for f in Path(UPLOAD_DIR).glob("*.webp")
        ) / (1024 * 1024)
        print(
            f"Logos done. resized+saved: {downloaded} | attached: {attached} | "
            f"placeholders: {fallbacks} | uploads .webp total: {total:.1f} MB"
        )
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run(limit=arg)
