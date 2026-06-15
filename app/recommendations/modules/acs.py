"""Acute Coronary Syndrome (ACS) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/acsLogic.ts (assessACS).

Based on the 2025 ACC/AHA/ACEP/NAEMSP/SCAI Guideline for the Management of
Patients With Acute Coronary Syndromes (Rao SV et al. Circulation. 2025).
"""

from __future__ import annotations

from app.recommendations.jslib import js_minutes_between, js_round, num, truthy

LOGIC_KEY = "acs"


def _classify_acs_type(data: dict) -> str:
    """Classify ACS type based on troponin and ECG findings."""
    if truthy(data.get("stSegmentElevation")) or truthy(data.get("newLBBB")):
        return "STEMI"
    if truthy(data.get("troponinElevated")):
        return "NSTEMI"
    return "UNSTABLE_ANGINA"


def _calculate_nste_risk_level(data: dict) -> str:
    """Calculate NSTE-ACS risk using simplified HEART score and troponin."""
    score = 0

    # Troponin elevation (most important)
    if truthy(data.get("troponinElevated")):
        score += 3
    else:
        score += 0

    # Age
    if num(data.get("age")) >= 65:
        score += 1

    # Risk factors
    if truthy(data.get("priorMI")) or truthy(data.get("priorPCI")) or truthy(data.get("priorCABG")):
        score += 1
    if truthy(data.get("diabetes")) or truthy(data.get("hypertension")):
        score += 1

    # Hemodynamics
    if num(data.get("killipClass")) >= 2:
        score += 2

    # ECG changes
    if truthy(data.get("stSegmentDepression")):
        score += 1
    if truthy(data.get("tWaveInversion")):
        score += 1

    # BNP elevation if available
    bnp = data.get("bNPLevel")
    if truthy(bnp) and num(bnp) > 100:
        score += 1

    if score >= 6:
        return "HIGH"
    if score >= 3:
        return "INTERMEDIATE"
    return "LOW"


def _assess_bleeding_risk(data: dict) -> str:
    """Assess bleeding risk using simplified PRECISE-DAPT and HAS-BLED."""
    score = 0

    age = num(data.get("age"))
    # Age
    if age >= 75:
        score += 2
    elif age >= 65:
        score += 1

    creatinine = num(data.get("creatinine"))
    # Renal function
    if creatinine > 2.0:
        score += 2
    elif creatinine > 1.5:
        score += 1

    hemoglobin = num(data.get("hemoglobin"))
    # Hemoglobin
    if hemoglobin < 10:
        score += 2
    elif hemoglobin < 11:
        score += 1

    # Prior stroke/TIA
    if truthy(data.get("priorStroke")) or truthy(data.get("priorTIA")):
        score += 2

    # Active bleeding or recent surgery
    if truthy(data.get("activeBleed")) or truthy(data.get("recentSurgery")):
        score += 2

    # Chronic kidney disease
    if truthy(data.get("chronicKidneyDisease")):
        score += 1

    # On oral anticoagulant
    if truthy(data.get("onOralAnticoagulant")):
        score += 1

    if score >= 5:
        return "HIGH"
    if score >= 2:
        return "MODERATE"
    return "LOW"


def _recommend_p2y12_inhibitor(data: dict, bleeding_risk: str) -> str:
    """Recommend P2Y12 inhibitor based on bleeding risk and patient factors."""
    # Contraindications to prasugrel/ticagrelor
    if (
        truthy(data.get("priorStroke"))
        or truthy(data.get("priorTIA"))
        or num(data.get("age")) >= 75
        or num(data.get("weight")) < 60
    ):
        return "CLOPIDOGREL"

    # High bleeding risk
    if bleeding_risk == "HIGH":
        return "CLOPIDOGREL"

    # STEMI: prefer prasugrel or ticagrelor
    if data.get("acsType") == "STEMI":
        return "PRASUGREL"

    # NSTEMI: ticagrelor preferred
    return "TICAGRELOR"


def _recommend_anticoagulant(data: dict, bleeding_risk: str) -> str:
    """Recommend anticoagulant based on renal function and bleeding risk."""
    creatinine = num(data.get("creatinine"))

    # High bleeding risk: consider fondaparinux
    if bleeding_risk == "HIGH":
        if creatinine <= 3.0:
            return "FONDAPARINUX"
        return "UFH"

    # Moderate bleeding risk: LMWH or UFH
    if bleeding_risk == "MODERATE":
        if creatinine > 2.0:
            return "UFH"
        return "LMWH"

    # Low bleeding risk: bivalirudin for PCI
    if data.get("acsType") == "STEMI" and truthy(data.get("canAccessCathLab")):
        return "BIVALIRUDIN"

    return "UFH"


def _recommend_nste_invasive_strategy(data: dict, risk_level: str) -> str:
    """Recommend invasive strategy for NSTE-ACS."""
    # High-risk: routine invasive within 24 hours
    if risk_level == "HIGH":
        return "ROUTINE_INVASIVE"

    # Intermediate-risk: routine invasive
    if risk_level == "INTERMEDIATE":
        return "ROUTINE_INVASIVE"

    # Low-risk: selective invasive with further risk stratification
    return "SELECTIVE_INVASIVE"


def _recommend_stemi_reperfusion(data: dict) -> str:
    """Recommend reperfusion strategy for STEMI."""
    # Primary PCI is preferred if available within 120 minutes
    if truthy(data.get("canAccessCathLab")):
        door_to_balloon = 90  # minutes
        symptom_onset_to_presentation = js_round(
            js_minutes_between(data.get("symptomOnsetTime"), data.get("presentationTime"))
        )

        # If total time to balloon <120 min, use PPCI
        if symptom_onset_to_presentation + door_to_balloon <= 120:
            return "PPCI"

    # Fibrinolytic if PPCI not available or delayed
    if not truthy(data.get("fibrinolyticContraindication")):
        return "FIBRINOLYTIC"

    # If both unavailable, refer for urgent PPCI
    return "PPCI"


def _recommend_vascular_access(data: dict) -> str:
    """Generate vascular access recommendation."""
    # Radial preferred for ACS to reduce bleeding
    if truthy(data.get("radialAccess")):
        return "Radial approach preferred (reduces bleeding and vascular complications)"

    if truthy(data.get("femurAccess")):
        return "Femoral approach acceptable if radial unavailable"

    return "Radial approach strongly recommended for ACS"


def assess(data: dict) -> dict:
    acs_type = _classify_acs_type(data)
    risk_level = "HIGH" if acs_type == "STEMI" else _calculate_nste_risk_level(data)
    bleeding_risk = _assess_bleeding_risk(data)
    p2y12 = _recommend_p2y12_inhibitor(data, bleeding_risk)
    anticoagulant = _recommend_anticoagulant(data, bleeding_risk)

    if acs_type == "STEMI":
        strategy = _recommend_stemi_reperfusion(data)
        time_to_reperfusion = 90 if strategy == "PPCI" else 30
    else:
        strategy = _recommend_nste_invasive_strategy(data, risk_level)
        time_to_reperfusion = 240 if strategy == "ROUTINE_INVASIVE" else 0

    recommendations: list[str] = []
    contraindications: list[str] = []
    special_considerations: list[str] = []

    # Generate recommendations
    recommendations.append(f"ACS Type: {acs_type}")
    recommendations.append(f"Risk Level: {risk_level}")
    recommendations.append(f"Recommended Strategy: {strategy}")
    recommendations.append(f"P2Y12 Inhibitor: {p2y12}")
    recommendations.append(f"Anticoagulant: {anticoagulant}")
    recommendations.append(_recommend_vascular_access(data))

    # Dual antiplatelet therapy (aspirin + P2Y12)
    recommendations.append(
        "Dual antiplatelet therapy (aspirin + P2Y12 inhibitor) for ≥12 months"
    )

    # High-intensity statin
    recommendations.append(
        "High-intensity statin therapy (atorvastatin 80 mg or rosuvastatin 40 mg daily)"
    )

    # Bleeding prevention
    if bleeding_risk == "HIGH":
        recommendations.append("Proton pump inhibitor for GI bleeding prevention")
        special_considerations.append(
            "High bleeding risk: consider ticagrelor monotherapy ≥1 month post-PCI"
        )

    # Cardiogenic shock
    if truthy(data.get("cardiogenicShock")):
        special_considerations.append(
            "Cardiogenic shock present: emergency revascularization of culprit vessel indicated"
        )
        special_considerations.append(
            "Consider mechanical circulatory support (microaxial flow pump) in selected cases"
        )

    # Anemia management
    hemoglobin = num(data.get("hemoglobin"))
    if hemoglobin < 10:
        special_considerations.append(
            f"Hemoglobin {_fmt_num(data.get('hemoglobin'))} g/dL: consider transfusion to maintain Hgb ≥10 g/dL"
        )

    # Contraindications
    if truthy(data.get("fibrinolyticContraindication")) and acs_type == "STEMI":
        contraindications.append("Fibrinolytic contraindication present")

    if truthy(data.get("priorStroke")) or truthy(data.get("priorTIA")):
        contraindications.append("Prior stroke/TIA: prasugrel contraindicated")

    return {
        "acsType": acs_type,
        "riskLevel": risk_level,
        "recommendedStrategy": strategy,
        "recommendedP2Y12": p2y12,
        "recommendedAnticoagulant": anticoagulant,
        "bleedingRisk": bleeding_risk,
        "timeToReperfusion": time_to_reperfusion,
        "recommendations": recommendations,
        "contraindications": contraindications,
        "specialConsiderations": special_considerations,
    }


def _fmt_num(x) -> str:
    """Render a number the way JS string interpolation would (e.g. 9 not 9.0)."""
    if isinstance(x, bool) or x is None:
        return str(x)
    if isinstance(x, (int, float)):
        if float(x).is_integer():
            return str(int(x))
        return repr(float(x))
    return str(x)
