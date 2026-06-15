"""Blepharoplasty / Ptosis Repair clinical decision logic.

Ported 1:1 from old_static_code/client/src/lib/blepharoplastyLogic.ts
(calculateBlepharoplasty​Score).

Based on: AAO-HNS Clinical Practice Guidelines; CMS LCD L34462; ASOPRS
Guidelines; Ophthalmology Society functional criteria.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float, to_bool

LOGIC_KEY = "blepharoplasty"

_REFERENCES = [
    "CMS LCD L34462. Blepharoplasty. Centers for Medicare & Medicaid Services — Coverage criteria: ≥12° superior visual field defect, MRD1 ≤2mm for ptosis, or functional impairment documented by visual field testing",
    "American Academy of Ophthalmology. Preferred Practice Pattern: Ptosis. 2018 — Classification and management of ptosis; MRD1 ≤2mm indicates functional ptosis requiring repair",
    "Cahill KV, Bradley EA, Meyer DR, et al. Functional Indications for Upper Eyelid Ptosis and Blepharoplasty Surgery. Ophthalmology. 2011;118(12):2510-2517. PMID: 21906817 — Evidence base for functional criteria in upper eyelid surgery",
    "Jacobs SW. Regarding the Schnur Scale and Blepharoplasty. Plast Reconstr Surg. 2002 — Visual field testing methodology for establishing functional blepharoplasty indication",
    "American Society of Ophthalmic Plastic and Reconstructive Surgery (ASOPRS). Position Statement on Functional Blepharoplasty. 2019 — Functional criteria and documentation requirements for insurance coverage",
]


def _n(x) -> float:
    """Raw numeric field (TS receives a real number; missing/NaN -> 0)."""
    v = parse_float(x)
    return 0.0 if math.isnan(v) else v


def _num_str(x) -> str:
    """Render a numeric field the way JS string interpolation does
    (``${x}`` of an integer-valued float prints without ``.0``)."""
    v = _n(x)
    return str(int(v)) if v == int(v) else str(v)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0
    functional_criteria_met = False

    marginal_reflex_distance = _n(data.get("marginalReflexDistance"))
    superior_visual_field_loss = _n(data.get("superiorVisualFieldLoss"))
    symptom_duration_months = _n(data.get("symptomDurationMonths"))
    asa = _n(data.get("asa"))

    ptosis_present = to_bool(data.get("ptosisPresent"))
    visual_field_defect = to_bool(data.get("visualFieldDefect"))
    dermatochalasis = to_bool(data.get("dermatochalasis"))
    visual_obstruction = to_bool(data.get("visualObstruction"))
    excess_skin_overhang = to_bool(data.get("excessSkinOverhang"))
    difficulty_reading = to_bool(data.get("difficultyReading"))
    difficulty_driving = to_bool(data.get("difficultyDriving"))
    headache_from_brow = to_bool(data.get("headacheFromBrowCompensation"))
    eye_strain = to_bool(data.get("eyeStrain"))
    difficulty_with_activities = to_bool(data.get("difficultyWithActivities"))
    ectropion = to_bool(data.get("ectropion"))
    entropion = to_bool(data.get("entropion"))
    lagophthalmos = to_bool(data.get("lagophthalmos"))
    dry_eye = to_bool(data.get("dryEye"))
    thyroid_eye_disease = to_bool(data.get("thyroidEyeDisease"))
    anticoagulation = to_bool(data.get("anticoagulation"))

    mrd_str = _num_str(data.get("marginalReflexDistance"))

    # Ptosis grade
    ptosis_grade = "N/A"
    if ptosis_present:
        if marginal_reflex_distance <= 1:
            ptosis_grade = "Severe ptosis (MRD1 ≤1mm)"
            score += 40
            functional_criteria_met = True
            key_findings.append(
                f"Severe ptosis: MRD1 {mrd_str}mm — functional criteria met; CMS LCD L34462 criterion satisfied"
            )
        elif marginal_reflex_distance <= 2:
            ptosis_grade = "Moderate ptosis (MRD1 ≤2mm)"
            score += 30
            functional_criteria_met = True
            key_findings.append(
                f"Moderate ptosis: MRD1 {mrd_str}mm — functional criteria met"
            )
        elif marginal_reflex_distance <= 3:
            ptosis_grade = "Mild ptosis (MRD1 3mm)"
            score += 15
            key_findings.append(
                f"Mild ptosis: MRD1 {mrd_str}mm — functional criteria borderline; visual field testing recommended"
            )
        else:
            ptosis_grade = "Normal (MRD1 >3mm)"
            key_findings.append(
                f"MRD1 {mrd_str}mm — within normal range; visual field testing required to establish functional indication"
            )

    svfl_str = _num_str(data.get("superiorVisualFieldLoss"))

    # Visual field loss — primary functional criterion
    if visual_field_defect and superior_visual_field_loss >= 12:
        score += 35
        functional_criteria_met = True
        key_findings.append(
            f"Superior visual field loss {svfl_str}° — meets CMS criterion of ≥12° superior visual field defect"
        )
    elif visual_field_defect and superior_visual_field_loss >= 8:
        score += 20
        key_findings.append(
            f"Superior visual field loss {svfl_str}° — borderline; most payers require ≥12° for coverage"
        )
    elif visual_field_defect:
        score += 10
        key_findings.append(
            "Visual field defect present — quantify with Humphrey or Goldmann perimetry"
        )

    # Dermatochalasis with visual obstruction
    if dermatochalasis and visual_obstruction:
        score += 25
        functional_criteria_met = True
        key_findings.append(
            "Dermatochalasis with visual obstruction — functional upper blepharoplasty indicated"
        )
    elif dermatochalasis and excess_skin_overhang:
        score += 15
        key_findings.append(
            "Dermatochalasis with skin touching/overhanging lashes — document visual field testing"
        )

    # Functional symptoms
    if difficulty_reading:
        score += 10
        key_findings.append("Difficulty reading due to visual obstruction")
    if difficulty_driving:
        score += 10
        key_findings.append("Difficulty driving due to visual obstruction")
    if headache_from_brow:
        score += 8
        key_findings.append("Frontalis overuse headaches from brow compensation for ptosis")
    if eye_strain:
        score += 5
        key_findings.append("Eye strain from compensatory brow elevation")
    if difficulty_with_activities:
        score += 8
        key_findings.append("Limitation of daily activities due to visual obstruction")

    # Duration
    if symptom_duration_months >= 12:
        score += 5
        key_findings.append(
            f"{_num_str(data.get('symptomDurationMonths'))} months of functional symptoms"
        )

    # Lower blepharoplasty / ectropion / entropion
    if ectropion:
        score += 30
        functional_criteria_met = True
        key_findings.append(
            "Ectropion — functional lower blepharoplasty/repair indicated; risk of corneal exposure"
        )
        warnings.append(
            "Ectropion — corneal exposure risk; ophthalmology consultation recommended"
        )
    if entropion:
        score += 30
        functional_criteria_met = True
        key_findings.append(
            "Entropion — functional repair indicated; risk of corneal abrasion from lash trichiasis"
        )
    if lagophthalmos:
        score += 25
        functional_criteria_met = True
        key_findings.append(
            "Lagophthalmos — incomplete eye closure; functional repair indicated to prevent corneal exposure keratopathy"
        )
        warnings.append(
            "Lagophthalmos — corneal exposure risk; lubrication and protective eyewear required pending repair"
        )

    # Risk factors
    if dry_eye:
        warnings.append(
            "Dry eye syndrome — increased risk of post-operative dry eye worsening; Schirmer test and ophthalmology evaluation recommended pre-operatively"
        )
    if thyroid_eye_disease:
        warnings.append(
            "Thyroid eye disease — surgery contraindicated during active disease phase; thyroid function and ophthalmology clearance required; wait ≥6 months after disease stabilization"
        )
        score -= 15
    if anticoagulation:
        warnings.append(
            "Anticoagulation — increased bleeding risk; coordinate with prescribing physician for peri-operative management"
        )
    if asa >= 4:
        warnings.append(
            "ASA Class IV — very high surgical risk; risk-benefit discussion required"
        )
        score -= 15

    score = max(0, min(100, score))

    if functional_criteria_met and score >= 40:
        recommendation = "Strongly Indicated (Functional)"
        coverage_expectation = (
            "Likely covered by Medicare and most commercial payers — functional criteria met. "
            "Document visual field testing, MRD measurements, and functional symptoms in prior authorization request."
        )
    elif functional_criteria_met or score >= 25:
        recommendation = "Indicated (Functional)"
        coverage_expectation = (
            "Coverage possible — borderline functional criteria. Obtain visual field testing with and without "
            "eyelid tape to document functional improvement. Document all functional symptoms thoroughly."
        )
    elif score >= 10:
        recommendation = "Cosmetic Only"
        coverage_expectation = (
            "Likely cosmetic — functional criteria not met. Insurance coverage unlikely without visual field "
            "testing demonstrating ≥12° superior field defect or MRD1 ≤2mm for ptosis."
        )
    else:
        recommendation = "Not Indicated"
        coverage_expectation = (
            "Not indicated at this time — insufficient functional criteria. Reassess if symptoms progress."
        )

    return {
        "candidacyScore": score,
        "recommendation": recommendation,
        "functionalCriteriaMet": functional_criteria_met,
        "ptosisGrade": ptosis_grade,
        "keyFindings": key_findings,
        "warnings": warnings,
        "coverageExpectation": coverage_expectation,
        "references": _REFERENCES,
    }
