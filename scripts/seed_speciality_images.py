"""Attach the bundled speciality photos (app/seed/specialities/*.png) to Speciality.image.

No network access: copies each bundled photo into UPLOAD_DIR (the runtime volume)
when missing, then points the matching Speciality at it. Idempotent — safe to run
on every startup.

Only the specialities listed in MAPPING are touched; the rest keep whatever image
they already have (the early specialities ship with curated sp_*.jpg images). The
mapping is keyed by the exact Speciality.title so the script never guesses.

    PYTHONPATH=/app python scripts/seed_speciality_images.py
"""

import shutil
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Speciality
from app.storage import UPLOAD_DIR

SEED_DIR = Path(__file__).resolve().parent.parent / "app" / "seed" / "specialities"

# Speciality.title -> bundled photo filename. This is the full legacy speciality
# asset set: each photo belongs to the speciality of the same name. Only titles
# present in the DB are touched, so deployments with a subset of these
# specialities (and any extra specialities not listed here) are handled cleanly.
MAPPING = {
    "Surgery & Surgical Oncology": "surgery.png",
    "ENT, Endocrine & Sleep Medicine": "ent.png",
    "Interventional Radiology": "radiology.png",
    "Cardiology & Interventional Cardiology": "cardiology.png",
    "Vascular Medicine & Surgery": "vascular.png",
    "Hematology": "hematology.png",
    "Neurosurgery & Neuro-Oncology": "neurosurgery.png",
    "Dermatology": "dermatology.png",
    "Neurology": "neurology.png",
    "Ophthalmology": "ophthalmology.png",
    "Gastroenterology & Interventional GI": "gastroenterology.png",
    "Pediatrics": "pediatrics.png",
    "Radiation Oncology": "radiation-oncology.png",
    "Psychiatry": "psychiatry.png",
    "Orthopedics & Spine Surgery": "orthopaedics.png",
    "Pain Medicine & Interventional Procedures": "pain-medicine.png",
    "General Surgery & GI Surgery": "general-surgery.png",
    "Plastic & Reconstructive Surgery": "plastic-surgery.png",
    "Urology & Male Reproductive Medicine": "urology.png",
    "Reproductive Endocrinology & Infertility": "reproductive.png",
}


def run() -> None:
    upload = Path(UPLOAD_DIR)
    upload.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    attached = 0
    missing_src = 0
    unmatched = 0
    try:
        for title, filename in MAPPING.items():
            src = SEED_DIR / filename
            if not src.exists():  # photo not bundled -> skip
                missing_src += 1
                continue

            dest = upload / filename
            if not dest.exists():
                shutil.copyfile(src, dest)

            sp = db.scalar(select(Speciality).where(Speciality.title == title))
            if sp is None:
                unmatched += 1
                continue
            # Speciality.image is an ImageType (storage object on read), so compare
            # the resolved filename rather than the raw attribute to stay idempotent.
            current = (getattr(sp.image, "name", None) or str(sp.image)) if sp.image else None
            if current != filename:
                sp.image = filename
                attached += 1
        db.commit()
        print(
            f"[seed_speciality_images] attached/updated: {attached} | "
            f"missing source: {missing_src} | unmatched title: {unmatched}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
