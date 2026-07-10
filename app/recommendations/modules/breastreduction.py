"""Breast Reduction (Reduction Mammoplasty) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/breastReductionLogic.ts
(calculateBreastReductionScore, with helpers calculateSchnurMinimum and
calculateBSA).
"""

from __future__ import annotations

import math

from app.recommendations.jslib import js_round, num, truthy

LOGIC_KEY = "breastreduction"

# Schnur Scale: minimum resection weight (grams) per breast based on BSA
# Reference: Schnur PL, et al. Ann Plast Surg. 1991;27(3):232-5
_SCHNUR_TABLE: list[tuple[float, int]] = [
    (1.5, 300), (1.6, 360), (1.7, 420), (1.8, 500), (1.9, 580),
    (2.0, 660), (2.1, 750), (2.2, 840), (2.3, 940), (2.4, 1040),
    (2.5, 1150),
]

_REFERENCES = [
    "Schnur PL, et al. Reduction Mammaplasty: An Outcome Study. Plast Reconstr Surg. 1997;100(4):875-883. PMID: 9290654 — Schnur Scale for determining minimum resection weight relative to BSA",
    "Kerrigan CL, et al. Reduction Mammaplasty: Defining Medical Necessity. Med Decis Making. 2002;22(3):208-217. PMID: 12058779 — Functional symptoms and quality of life improvement following reduction mammoplasty",
    "American Society of Plastic Surgeons. Evidence-Based Clinical Practice Guideline: Reduction Mammaplasty. 2011 — ASPS guidelines for medical necessity criteria",
    "CMS LCD L35041. Reduction Mammaplasty. Centers for Medicare & Medicaid Services — Medicare coverage criteria including Schnur Scale and conservative treatment requirements",
    "Saariniemi KM, et al. Reduction Mammaplasty Improves Quality of Life, Self-Image and Physical Symptoms. J Plast Surg Hand Surg. 2014;48(4):239-244. PMID: 24397332 — Significant improvement in pain, posture, and quality of life following reduction mammoplasty",
]


def _to_fixed(value: float, digits: int) -> str:
    """JS ``Number.prototype.toFixed`` — round half away from zero."""
    factor = 10 ** digits
    rounded = math.floor(abs(value) * factor + 0.5) / factor
    if value < 0:
        rounded = -rounded
    return f"{rounded:.{digits}f}"


def calculate_schnur_minimum(bsa_m2: float) -> int:
    if bsa_m2 <= 1.5:
        return 300
    if bsa_m2 >= 2.5:
        return 1150
    for i in range(len(_SCHNUR_TABLE) - 1):
        bsa1, g1 = _SCHNUR_TABLE[i]
        bsa2, g2 = _SCHNUR_TABLE[i + 1]
        if bsa_m2 >= bsa1 and bsa_m2 <= bsa2:
            return js_round(g1 + ((bsa_m2 - bsa1) / (bsa2 - bsa1)) * (g2 - g1))
    return 500


def calculate_bsa(height_inches: float, weight_lbs: float) -> float:
    # Mosteller formula: BSA = sqrt((height_cm * weight_kg) / 3600)
    height_cm = height_inches * 2.54
    weight_kg = weight_lbs * 0.453592
    return math.sqrt((height_cm * weight_kg) / 3600)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    key_findings: list[str] = []
    score = 0

    bsa_input = num(data.get("bsaM2"), 0)
    height = num(data.get("height"), 0)
    weight = num(data.get("weight"), 0)
    estimated_resection = num(data.get("estimatedResectionGrams"), 0)
    pain_level = num(data.get("painLevel"), 0)
    symptom_duration = num(data.get("symptomDurationMonths"), 0)
    pt_duration = num(data.get("ptDurationMonths"), 0)
    weight_loss_months = num(data.get("weightLossAttemptMonths"), 0)
    bmi = num(data.get("bmi"), 0)
    if bmi <= 0 and height > 0 and weight > 0:
        # Legacy form auto-computed BMI in the height/weight onChange handlers
        # (BreastReductionCompass.tsx: (weight/(height*height))*703, toFixed(1),
        #  height in inches, weight in lbs); the seeded form submits only height
        # and weight, so reproduce it. floor(x*10+0.5)/10 == JS toFixed(1) for x>0.
        bmi = math.floor((weight / (height * height)) * 703 * 10 + 0.5) / 10
    asa = num(data.get("asa"), 0)

    # Calculate BSA and Schnur minimum if not provided
    bsa = bsa_input if bsa_input > 0 else calculate_bsa(height, weight)
    schnur_min = calculate_schnur_minimum(bsa)
    schnur_ratio = estimated_resection / schnur_min if estimated_resection > 0 else 0

    if schnur_ratio >= 1.0:
        schnur_category = "Clearly Eligible"
        score += 35
        key_findings.append(
            f"Estimated resection {_fmt_num(estimated_resection)}g per breast — meets Schnur Scale minimum of {schnur_min}g for BSA {_to_fixed(bsa, 2)}m²"
        )
    elif schnur_ratio >= 0.5:
        schnur_category = "Borderline"
        score += 15
        key_findings.append(
            f"Estimated resection {_fmt_num(estimated_resection)}g per breast — borderline for Schnur Scale (minimum {schnur_min}g for BSA {_to_fixed(bsa, 2)}m²); symptom documentation critical"
        )
    elif estimated_resection == 0:
        schnur_category = "Borderline"
        key_findings.append(
            "Resection weight estimate not provided — document estimated resection weight per breast for payer review"
        )
    else:
        schnur_category = "Not Eligible by Weight Alone"
        key_findings.append(
            f"Estimated resection {_fmt_num(estimated_resection)}g per breast — below Schnur Scale minimum of {schnur_min}g; functional symptoms must be documented"
        )

    # Functional symptoms
    symptoms = [
        (data.get("neckPain"), "Neck pain attributed to macromastia"),
        (data.get("shoulderPain"), "Shoulder pain attributed to macromastia"),
        (data.get("backPain"), "Back pain attributed to macromastia"),
        (data.get("shoulderGrooving"), "Bra strap shoulder grooving"),
        (data.get("intertrigo"), "Inframammary intertrigo / skin breakdown"),
        (data.get("posturalProblems"), "Postural problems / kyphosis"),
        (data.get("headaches"), "Headaches attributed to macromastia"),
        (data.get("numbness"), "Upper extremity numbness / paresthesias"),
        (data.get("limitedActivity"), "Limited physical activity due to breast size"),
    ]

    active = [label for field, label in symptoms if truthy(field)]
    symptom_count = len(active)
    for label in active:
        key_findings.append(label)

    if symptom_count >= 4:
        score += 30
    elif symptom_count >= 2:
        score += 20
    elif symptom_count >= 1:
        score += 10

    # Pain level
    if pain_level >= 7:
        score += 15
        key_findings.append(f"Pain level {_fmt_num(pain_level)}/10 — significant symptom burden")
    elif pain_level >= 4:
        score += 8

    # Symptom duration
    if symptom_duration >= 12:
        score += 10
        key_findings.append(
            f"{_fmt_num(symptom_duration)} months of symptoms — chronic macromastia-related symptoms"
        )
    elif symptom_duration >= 6:
        score += 5

    # Conservative treatment
    conservative_treatment_met = False
    if truthy(data.get("triedPhysicalTherapy")) and pt_duration >= 3:
        score += 15
        conservative_treatment_met = True
        key_findings.append(
            f"Physical therapy completed ({_fmt_num(pt_duration)} months) — conservative treatment requirement met"
        )
    elif truthy(data.get("triedPhysicalTherapy")):
        score += 8
        key_findings.append(
            f"Physical therapy attempted ({_fmt_num(pt_duration)} months) — most payers require ≥3 months"
        )

    if truthy(data.get("triedSupportiveBra")):
        score += 5
        key_findings.append("Supportive bra tried — conservative treatment documented")
    if truthy(data.get("triedMedications")):
        score += 5
        key_findings.append("NSAIDs / medications tried for pain management")

    if truthy(data.get("triedWeightLoss")) and weight_loss_months >= 6:
        score += 5
        key_findings.append(
            f"Weight loss attempted ({_fmt_num(weight_loss_months)} months) — some payers require weight loss attempt"
        )

    # Risk factors
    if truthy(data.get("smoking")):
        warnings.append(
            "Active smoking — significantly increases wound complications, fat necrosis, and skin flap loss; smoking cessation ≥4 weeks pre-operatively strongly recommended"
        )
        score -= 5

    if truthy(data.get("diabetes")):
        warnings.append(
            "Diabetes — increased wound healing complications; optimize glycemic control pre-operatively (HbA1c <8%)"
        )

    if bmi >= 40:
        warnings.append(
            f"BMI {_fmt_num(bmi)} — morbid obesity increases surgical risk and may affect payer coverage; some payers require BMI <35 or weight loss attempt"
        )
        score -= 10
    elif bmi >= 35:
        warnings.append(
            f"BMI {_fmt_num(bmi)} — obesity increases surgical risk; some payers require BMI <35"
        )
        score -= 5

    if asa >= 4:
        warnings.append("ASA Class IV — very high surgical risk; risk-benefit discussion required")
        score -= 15

    score = max(0, min(100, score))

    if score >= 60:
        recommendation = "Strongly Indicated"
    elif score >= 35:
        recommendation = "Indicated"
    elif score >= 15:
        recommendation = "Consider"
    else:
        recommendation = "Not Indicated"

    return {
        "candidacyScore": score,
        "recommendation": recommendation,
        "schnurCategory": schnur_category,
        "keyFindings": key_findings,
        "warnings": warnings,
        "conservativeTreatmentMet": conservative_treatment_met,
        "references": _REFERENCES,
    }


def _fmt_num(value: float) -> str:
    """Render a number the way JS string interpolation does: integers
    without a trailing ``.0``."""
    if value == int(value):
        return str(int(value))
    return str(value)
