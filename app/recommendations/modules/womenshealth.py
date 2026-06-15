"""Women's Health Clinical Compass: Pelvic Venous Disorder (PeVD) scoring.

Ported 1:1 from old_static_code/client/src/lib/womensHealthLogic.ts
(computePeVDScore). PeVD / Pelvic Congestion Syndrome assessment synthesising
ACOG, SIR, and AVFS diagnostic criteria.

The TypeScript entry takes a nested ``AssessmentData`` (symptoms / hemodynamics
/ anatomy), but the submitted form delivers the interface leaf fields flat. We
read the leaf field names directly; the scoring is identical.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import intnum, js_round, parse_float, truthy

LOGIC_KEY = "womenshealth"


def assess(data: dict) -> dict:
    score: float = 0.0
    max_score = 10
    criteria_met_count = 0
    criteria_total_count = 10

    # ── Symptom scoring ──────────────────────────────────────────────
    # Chronic pelvic pain >6 months is the hallmark presentation
    if truthy(data.get("chronicPelvicPain")):
        score += 1
        criteria_met_count += 1

    # Orthostatic exacerbation is characteristic of venous etiology
    if truthy(data.get("exacerbatedByStanding")):
        score += 1
        criteria_met_count += 1

    # Postcoital pain/dyspareunia strongly associated with PCS
    if truthy(data.get("postcoitalPain")):
        score += 1
        criteria_met_count += 1

    # Vulvar varicosities are a specific exam finding
    if truthy(data.get("vulvarVaricosities")):
        score += 0.5

    # Premenstrual worsening reflects hormonal influence on venous tone
    if truthy(data.get("premenstrualWorsening")):
        score += 0.5

    # Multiparity (>=2) is a significant risk factor
    if intnum(data.get("gravidity")) >= 2:
        score += 0.5
        criteria_met_count += 1

    # ── Hemodynamic scoring ──────────────────────────────────────────
    # Ovarian vein diameter thresholds:
    #   >=5mm = suggestive, >=6mm = diagnostic threshold, >=8mm = severe
    lov_diam = parse_float(data.get("lovDiameter"))
    if not math.isnan(lov_diam):
        if lov_diam >= 8:
            score += 2
            criteria_met_count += 1
        elif lov_diam >= 6:
            score += 1.5
            criteria_met_count += 1
        elif lov_diam >= 5:
            score += 0.5

    # Reflux duration >1 second on Valsalva = pathological
    lov_reflux = parse_float(data.get("lovRefluxDuration"))
    if not math.isnan(lov_reflux) and lov_reflux > 1000:
        score += 1
        criteria_met_count += 1

    # Cross-pelvic collateral flow indicates advanced incompetence
    if data.get("crossPelvicFlow") == "present":
        score += 1
        criteria_met_count += 1

    # ── Anatomy scoring ──────────────────────────────────────────────
    # Pelvic varicosities confirmed on imaging
    if truthy(data.get("pelvicVaricosities")):
        score += 1
        criteria_met_count += 1

    # Dilated arcuate veins traversing myometrium
    if data.get("dilatedArcuateVeins") == "pronounced":
        score += 0.5
        criteria_met_count += 1
    elif data.get("dilatedArcuateVeins") == "mild":
        score += 0.25

    normalized = min(score / max_score, 1)

    # ── LOV incompetence assessment ──────────────────────────────────
    # Combined diameter + reflux criteria. NB: NaN comparisons are False in
    # both JS and Python, so the missing-value behaviour matches.
    if lov_diam >= 6 and lov_reflux > 1000:
        lov_incompetence = "detected"
    elif lov_diam >= 5 or lov_reflux > 500:
        lov_incompetence = "inconclusive"
    else:
        lov_incompetence = "absent"

    # ── Nutcracker assessment ────────────────────────────────────────
    # Aortomesenteric angle <25 deg strongly suggests Nutcracker
    # Angle 25-35 deg is borderline
    nut_angle = parse_float(data.get("nutcrackerAngle"))
    if not math.isnan(nut_angle) and nut_angle < 25:
        nutcracker_risk = "detected"
    elif not math.isnan(nut_angle) and nut_angle < 35:
        nutcracker_risk = "inconclusive"
    else:
        nutcracker_risk = "absent"

    arcuate = data.get("dilatedArcuateVeins")
    if truthy(data.get("pelvicVaricosities")):
        pelvic_varicosities = "confirmed"
    elif arcuate != "none" and arcuate != "":
        pelvic_varicosities = "suspected"
    else:
        pelvic_varicosities = "absent"

    if normalized >= 0.7:
        confidence = "high"
    elif normalized >= 0.4:
        confidence = "moderate"
    else:
        confidence = "low"

    recommendation = ""
    treatment_options: list[str] = []
    label = ""
    color = "destructive"

    if normalized >= 0.7:
        label = "Criteria Met for PeVD"
        color = "primary"
        if lov_incompetence == "detected":
            tail = (
                "Left Ovarian Vein embolization is clinically indicated based on "
                "current hemodynamic profile."
            )
        else:
            tail = "Further venographic confirmation recommended before intervention."
        recommendation = (
            "Criteria met for Pelvic Venous Disorder (PeVD; formerly termed Pelvic "
            f"Congestion Syndrome). {tail}"
        )
        treatment_options.append("Ovarian vein embolization")
        treatment_options.append("Sclerotherapy")
        if nutcracker_risk == "detected":
            treatment_options.append("Renal vein stenting (Nutcracker)")
    elif normalized >= 0.4:
        label = "Moderate Suspicion for PeVD"
        color = "warning"
        recommendation = (
            "Moderate suspicion for Pelvic Venous Disorder (PeVD). Consider "
            "diagnostic venography with provocation maneuvers for definitive "
            "assessment."
        )
        treatment_options.append("Diagnostic venography")
        treatment_options.append("MR venography")
        treatment_options.append("Conservative management trial")
    else:
        label = "Low Probability for PeVD"
        color = "destructive"
        recommendation = (
            "Low probability for Pelvic Venous Disorder (PeVD) based on current "
            "data. Consider alternative differential diagnoses including "
            "endometriosis, adenomyosis, or musculoskeletal etiologies."
        )
        treatment_options.append("Expanded differential workup")
        treatment_options.append("Pelvic MRI")

    return {
        "congestionScore": normalized,
        "confidence": confidence,
        "lovIncompetence": lov_incompetence,
        "nutcrackerRisk": nutcracker_risk,
        "pelvicVaricosities": pelvic_varicosities,
        "recommendation": recommendation,
        "treatmentOptions": treatment_options,
        "label": label,
        "summary": recommendation,
        "color": color,
        "score": js_round(normalized * 100),
        "criteriaMetCount": criteria_met_count,
        "criteriaTotalCount": criteria_total_count,
    }
