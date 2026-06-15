"""One-off migration: load rendered appeal-letter templates (from the legacy
old_static_code React pages) into Module.appeal_letter.

The letters were rendered to /tmp/letters.json by the esbuild-based extractor,
with all [PLACEHOLDER] / ${var} fill-ins normalized to [[placeholder]] form.

Run:  python scripts/migrate_appeal_letters.py [path/to/letters.json]
"""

from __future__ import annotations

import json
import sys

from app.database import SessionLocal
from app.models import Module

# Legacy appeal-letter filename (without .tsx) -> module title in the DB.
FILE_TO_TITLE = {
    "AcneAppealLetter": "Acne Vulgaris Clinical Compass",
    "AFAblationAppealLetter": "AF Ablation Clinical Compass",
    "AMDAppealLetter": "Age-Related Macular Degeneration",
    "ArtificialDiscAppealLetter": "Artificial Disc Replacement Clinical Compass",
    "AtherectomyAppealLetter": "Peripheral Atherectomy Clinical Compass",
    "AtopicDermatitisAppealLetter": "Atopic Dermatitis Clinical Compass",
    "BariatricAppealLetter": "Bariatric Surgery Clinical Compass",
    "BiliaryStricturesAppealLetter": "Biliary Strictures Clinical Compass",
    "BlepharoplastyAppealLetter": "Blepharoplasty / Ptosis Repair Clinical Compass",
    "BoneCancerAppealLetter": "Bone Cancer Interventional Oncology Clinical Compass",
    "BrainMetastasesAppealLetter": "Brain Metastases Clinical Compass",
    "BreastReductionAppealLetter": "Breast Reduction Clinical Compass",
    "CCMAppealLetter": "Cerebral Cavernous Malformation Compass",
    "CentralSleepApneaAppealLetter": "Central Sleep Apnea Clinical Compass",
    "CholecystectomyAppealLetter": "Cholecystectomy Clinical Compass",
    "ChronicInsomniaAppealLetter": "Chronic Insomnia Clinical Compass",
    "ChronicPancreatitisAppealLetter": "Chronic Pancreatitis Clinical Compass",
    "CRCScreeningAppealLetter": "CRC Screening Clinical Compass",
    "DyslipidemiaDSAppealLetter": "Dyslipidemia Clinical Compass",
    "EmbryoCryoAppealLetter": "Embryo Cryopreservation Clinical Compass",
    "EndovenousAblationAppealLetter": "Endovenous Ablation Clinical Compass",
    "EpiduralSteroidAppealLetter": "Epidural Steroid Injection Clinical Compass",
    "FacetJointAppealLetter": "Facet Joint Injection Clinical Compass",
    "GAEAppealLetter": "Geniculate Artery Embolization Clinical Compass",
    "GastroparesisAppealLetter": "Gastroparesis Clinical Compass",
    "GenderAffirmingUroAppealLetter": "Gender-Affirming Urologic Procedures Clinical Compass",
    "GestationalCarrierAppealLetter": "Gestational Carrier Clinical Compass",
    "GlaucomaAppealLetter": "Glaucoma",
    "HerniaAppealLetter": "Hernia Repair Clinical Compass",
    "HighMyopiaAppealLetter": "High Myopia / Pathologic Myopia",
    "ICSIAppealLetter": "Intracytoplasmic Sperm Injection Clinical Compass",
    "IVFAppealLetter": "In Vitro Fertilization Clinical Compass",
    "LAACAppealLetter": "LAAC / Watchman Clinical Compass",
    "LiverTumorAppealLetter": "Liver Tumor Clinical Compass",
    "LowGradeGliomaAppealLetter": "Low-Grade Glioma Clinical Compass",
    "MeniscusRepairAppealLetter": "Meniscus Repair Clinical Compass",
    "MensHealthAppealLetter": "Prostatic Artery Embolization Clinical Compass",
    "MigraineAppealLetter": "Migraine",
    "MultipleSclerosisAppealLetter": "Multiple Sclerosis",
    "NarcolepsyAppealLetter": "Narcolepsy Clinical Compass",
    "OSAAppealLetter": "OSA Clinical Compass",
    "OSAObesityAppealLetter": "OSA + Obesity Clinical Compass",
    "ObesityAppealLetter": "Obesity Treatment Clinical Compass",
    "OocyteFreezeAppealLetter": "Oocyte Cryopreservation Clinical Compass",
    "OvulationInductionAppealLetter": "Ovulation Induction Clinical Compass",
    "PADAppealLetter": "PAD Revascularization Clinical Compass",
    "PADQualityAppealLetter": "PAD Clinical Performance & Quality Measures Clinical Compass",
    "ParkinsonsAppealLetter": "Parkinson's Disease",
    "PAVFAppealLetter": "Percutaneous AV Fistula Clinical Compass",
    "PCIAppealLetter": "Elective PCI Clinical Compass",
    "PediatricObesityAppealLetter": "Pediatric Obesity Clinical Compass",
    "PeyroniesAppealLetter": "Peyronie's Disease Surgery Clinical Compass",
    "PGTAppealLetter": "Preimplantation Genetic Testing Clinical Compass",
    "PituitaryAdenomaAppealLetter": "Pituitary Adenoma Clinical Compass",
    "PortalHypertensionAppealLetter": "Portal Hypertension Clinical Compass",
    "PsoriasisAppealLetter": "Psoriasis Clinical Compass",
    "RectalCancerAppealLetter": "Rectal Cancer Clinical Compass",
    "RenalCryoablationAppealLetter": "Renal Cryoablation Clinical Compass",
    "RFAAppealLetter": "Radiofrequency Ablation Clinical Compass",
    "RLSPLMDAppealLetter": "RLS / PLMD Clinical Compass",
    "RotatorCuffAppealLetter": "Rotator Cuff Repair Clinical Compass",
    "SacroplastyAppealLetter": "Sacroplasty Clinical Compass",
    "SclerotherapyAppealLetter": "Sclerotherapy Clinical Compass",
    "SCSAppealLetter": "Spinal Cord Stimulator Clinical Compass",
    "SpinalFusionAppealLetter": "Spinal Fusion Clinical Compass",
    "SpineAntithromboticAppealLetter": "Spine Antithrombotic Compass",
    "SpineAppealLetter": "Spine Surgery Clinical Compass",
    "TESEAppealLetter": "TESE / Micro-TESE Clinical Compass",
    "THAAppealLetter": "Total Hip Arthroplasty Clinical Compass",
    "TherapeuticEUSAppealLetter": "Therapeutic EUS Clinical Compass",
    "ThyroidNoduleAppealLetter": "Thyroid Nodule Clinical Compass",
    "TKAAppealLetter": "Total Knee Arthroplasty Clinical Compass",
    "VaricoceleAppealLetter": "Varicocele Embolization Clinical Compass",
    "VaricocelectomyAppealLetter": "Varicocelectomy Clinical Compass",
    "VasectomyReversalAppealLetter": "Vasectomy Reversal Clinical Compass",
    "VertebroplastyAppealLetter": "Vertebroplasty / Kyphoplasty Clinical Compass",
    "VestibularSchwannomaAppealLetter": "Vestibular Schwannoma Clinical Compass",
    "VTEAppealLetter": "Venous Thromboembolism Clinical Compass",
    "WomensHealthAppealLetter": "Women's Health Clinical Compass",
    "Y90AppealLetter": "Y-90 Radioembolization Clinical Compass",
}


def _ascii(name: str) -> str:
    """Normalize legacy filenames that contain look-alike Cyrillic letters."""
    return name.replace("т", "t").replace("с", "c")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/letters.json"
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    # Normalize keys: strip ".tsx", transliterate look-alikes.
    letters = {_ascii(k.removesuffix(".tsx")): v for k, v in raw.items()}

    db = SessionLocal()
    try:
        by_title = {m.title: m for m in db.query(Module).all()}
        updated, missing_module, missing_letter = [], [], []

        for fname, title in FILE_TO_TITLE.items():
            module = by_title.get(title)
            letter = letters.get(fname)
            if module is None:
                missing_module.append((fname, title))
                continue
            if not letter:
                missing_letter.append(fname)
                continue
            module.appeal_letter = letter
            updated.append(title)

        db.commit()

        print(f"Updated {len(updated)} modules with appeal letters.")
        if missing_module:
            print(f"\n{len(missing_module)} mapped titles not found in DB:")
            for fname, title in missing_module:
                print(f"  - {fname} -> {title!r}")
        if missing_letter:
            print(f"\n{len(missing_letter)} files had no rendered letter:")
            for fname in missing_letter:
                print(f"  - {fname}")

        unmapped = [k for k in letters if k not in FILE_TO_TITLE]
        if unmapped:
            print(f"\n{len(unmapped)} rendered letters had no mapping:")
            for k in unmapped:
                print(f"  - {k}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
