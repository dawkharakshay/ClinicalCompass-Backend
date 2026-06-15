"""Gender-Affirming Urologic Procedures Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/GenderAffirmingUroCompass.tsx
(inline ``evaluate(inputs)`` — no separate *Logic.ts file exists for this module).

WPATH SOC-8 (2022) criteria assessment for gender-affirming urologic surgery.
"""

from __future__ import annotations

import re

from app.recommendations.jslib import includes, num, truthy

LOGIC_KEY = "genderaffirminguro"

_REFERENCES = [
    "Coleman E, et al. Standards of Care for the Health of Transgender and Gender Diverse People, Version 8. Int J Transgend Health. 2022;23(Suppl 1):S1-S259.",
    "WPATH SOC-8: Chapter 12 — Surgical and Postoperative Care. Int J Transgend Health. 2022.",
    "American Urological Association. Policy Statement: Transgender and Gender-Diverse Health Care. 2021.",
    "Raffaini M, et al. Gender-affirming surgery: a systematic review of outcomes. J Plast Reconstr Aesthet Surg. 2021.",
    "Deutsch MB, ed. Guidelines for the Primary and Gender-Affirming Care of Transgender and Gender Nonbinary People. UCSF, 2016.",
]

_HORMONE_PROCEDURES = ["vaginoplasty", "phalloplasty", "metoidioplasty"]


def _title_case_procedure(proc: str) -> str:
    """Reproduce TS: .replace(/_/g, " ").replace(/\\b\\w/g, c => c.toUpperCase()).

    Replaces underscores with spaces, then uppercases the first word-character
    of every word (a word boundary followed by a word char).
    """
    s = proc.replace("_", " ")
    return re.sub(r"\b\w", lambda m: m.group(0).upper(), s)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    met_criteria: list[str] = []
    missing_criteria: list[str] = []

    proposed_procedure = data.get("proposedProcedure") or ""
    duration_months = num(data.get("durationMonths"), 0)
    hormone_therapy_months = num(data.get("hormoneTherapyMonths"), 0)
    patient_age = num(data.get("patientAge"), 0)

    # WPATH SOC-8 criteria assessment
    if truthy(data.get("diagnosisGenderDysphoria")):
        met_criteria.append("Gender dysphoria diagnosis documented")
    else:
        missing_criteria.append("Gender dysphoria diagnosis required (DSM-5 F64.0 or ICD-11 HA60)")

    if truthy(data.get("persistentDysphoria")) and duration_months >= 6:
        met_criteria.append(f"Persistent gender dysphoria for {_fmt_num(duration_months)} months")
    else:
        missing_criteria.append("Persistent, well-documented gender dysphoria required")

    if truthy(data.get("mentalHealthEvaluation")) and truthy(data.get("mentalHealthClearance")):
        met_criteria.append("Mental health evaluation with surgical clearance obtained")
    else:
        missing_criteria.append("Mental health evaluation and clearance required")

    if truthy(data.get("comorbidMentalHealthTreated")):
        met_criteria.append("Comorbid mental health conditions treated/stable")
    else:
        missing_criteria.append("Comorbid mental health conditions must be stable before surgery")

    if truthy(data.get("informedConsent")):
        met_criteria.append("Informed consent documented")
    else:
        missing_criteria.append("Informed consent process required")

    # Hormone therapy requirement (procedure-specific)
    requires_hormones = includes(_HORMONE_PROCEDURES, proposed_procedure)
    if requires_hormones:
        if truthy(data.get("hormoneTherapyContraindicated")):
            met_criteria.append("Hormone therapy contraindicated — documented exception")
        elif hormone_therapy_months >= 12:
            met_criteria.append(f"{_fmt_num(hormone_therapy_months)} months of hormone therapy completed")
        else:
            missing_criteria.append("≥12 months of hormone therapy required before genital surgery (WPATH SOC-8)")

    # Age
    if patient_age < 18:
        warnings.append(
            "Patient is a minor: additional criteria apply per WPATH SOC-8 Chapter 6 (Adolescents). "
            "Parental consent and multidisciplinary team required."
        )

    all_met = len(missing_criteria) == 0
    recommendation = "indicated" if all_met else "not_yet_indicated"
    procedure = _title_case_procedure(proposed_procedure)

    rationale.append(
        "WPATH SOC-8 (2022) provides the current standard of care for gender-affirming surgical procedures."
    )
    rationale.append(
        "AUA Policy Statement (2021) supports access to gender-affirming urologic care as medically necessary."
    )

    if truthy(data.get("twoLettersObtained")):
        rationale.append(
            "Two letters of support from qualified mental health professionals obtained — meets most payer requirements."
        )
    else:
        warnings.append(
            "Most payers require 2 letters of support from qualified mental health professionals "
            "(WPATH SOC-7 legacy requirement still used by many insurers)."
        )

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "metCriteria": met_criteria,
        "missingCriteria": missing_criteria,
        "warnings": warnings,
        "rationale": rationale,
        "references": references,
    }


def _fmt_num(x: float) -> str:
    """Render a number the way JS template literals do (no trailing .0 for ints)."""
    return str(int(x)) if float(x).is_integer() else str(x)
