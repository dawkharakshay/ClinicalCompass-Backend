"""Dyslipidemia Clinical Compass treatment-plan engine.

Ported 1:1 from old_static_code/client/src/lib/dyslipidemia-logic.ts
(generateDyslipidemiaPlan and all helpers).

Based on the 2026 ACC/AHA/AACVPR/ABC/ACPM/ADA/AGS/APhA/ASPC/NLA/PCNA Guideline
on the Management of Dyslipidemia.
"""

from __future__ import annotations

import math

from app.recommendations.card import build_card
from app.recommendations.jslib import num, truthy

LOGIC_KEY = "dyslipidemiads"

# Follow-up monitoring guidance shown in the old results UI's "Follow-up
# Monitoring" card (DyslipidemiaDSResults.tsx). The generic mapper only surfaced
# the bare ``monitoringInterval`` value, dropping these steps — restore them.
_MONITORING_STEPS = [
    "Check lipid panel after 4-12 weeks to assess response",
    "Adjust therapy if LDL-C not at goal",
    "Monitor for statin-related muscle symptoms",
    "Annual assessment of adherence and tolerability",
]

# Static reference list surfaced as the card's "Supporting Guidelines & Evidence"
# section (auto-attached by app.recommendations.registry.get_evidence). Ported 1:1
# from the inline `const dyslipidemiReferences = [...]` array in
# old_static_code/client/src/pages/DyslipidemiaDSCompass.tsx. URL-only entries fold
# the link into the description since _normalize_evidence keeps only
# title/source/description/pmid.
EVIDENCE = [
    {
        "title": "2026 ACC/AHA/AACVPR/ABC/ACPM/ADA/AGS/APhA/ASPC/NLA/PCNA Guideline on the Management of Dyslipidemia",
        "source": "Grundy SM, Stone NJ, Bailey AL, et al.",
        "description": "J Am Coll Cardiol. 2026 (in press). Comprehensive guideline addressing evaluation, management, and monitoring of dyslipidemia including LDL-C, HDL-C, triglycerides, and Lp(a). Covers primordial, primary, and secondary prevention. Available at: jacc.org/guidelines/dyslipidemia.",
        "pmid": None,
    },
    {
        "title": "2018 AHA/ACC/AACVPR/AAPA/ABC/ACPM/ADA/AGS/APhA/ASPC/NLA/PCNA Guideline on the Management of Blood Cholesterol",
        "source": "Grundy SM, Stone NJ, Bailey AL, et al.",
        "description": "J Am Coll Cardiol. 2019;73(24):e285–e350. PMID: 30423393",
        "pmid": "30423393",
    },
    {
        "title": "FOURIER Trial: Evolocumab and Clinical Outcomes in Patients With Cardiovascular Disease",
        "source": "Sabatine MS, Giugliano RP, Keech AC, et al.",
        "description": "N Engl J Med. 2017;376(18):1713–1722. PMID: 28304224",
        "pmid": "28304224",
    },
    {
        "title": "ODYSSEY OUTCOMES Trial: Alirocumab and Cardiovascular Outcomes After ACS",
        "source": "Schwartz GG, Steg PG, Szarek M, et al.",
        "description": "N Engl J Med. 2018;379(22):2097–2107. PMID: 30403574",
        "pmid": "30403574",
    },
    {
        "title": "ORION-10 Trial: Inclisiran in Patients at High Cardiovascular Risk With Elevated LDL Cholesterol",
        "source": "Ray KK, Wright RS, Kallend D, et al.",
        "description": "N Engl J Med. 2020;382(16):1507–1519. PMID: 32187462",
        "pmid": "32187462",
    },
]


def _js_number(x: float) -> str:
    """Render a number the way JS string interpolation does: an integral
    float prints without a trailing ``.0`` (e.g. 200 -> "200", 200.5 ->
    "200.5")."""
    if x == int(x):
        return str(int(x))
    return repr(x)


def _lipid_panel(data: dict) -> dict:
    """Return the lipid panel.

    The TypeScript ``PatientData`` nests lipids under ``lipidPanel``; the
    seeded ClinicalCompass form submits them flat (top-level ``ldlC``, ``hdlC``,
    ``triglycerides``, ``totalCholesterol``, ``lpa``). Support both: prefer an
    explicit nested ``lipidPanel`` when present, otherwise read the flat keys.
    """
    panel = data.get("lipidPanel")
    if panel:
        return panel
    return {
        "ldlC": data.get("ldlC"),
        "hdlC": data.get("hdlC"),
        "triglycerides": data.get("triglycerides"),
        "totalCholesterol": data.get("totalCholesterol"),
        "lpa": data.get("lpa"),
    }


def determine_prevention_category(patient: dict) -> str:
    if (
        truthy(patient.get("priorMI"))
        or truthy(patient.get("priorStroke"))
        or truthy(patient.get("priorPAD"))
        or truthy(patient.get("aorticAneurysm"))
    ):
        return "secondary"
    if truthy(patient.get("diabetic")) or num(patient.get("age"), 0) >= 40:
        return "primary"
    return "primordial"


def calculate_ascvd_risk(patient: dict) -> float:
    risk = 0.0
    panel = _lipid_panel(patient)
    age = num(patient.get("age"), 0)

    # Age contribution
    if patient.get("sex") == "male":
        risk += (age - 45) * 0.5
    else:
        risk += (age - 55) * 0.5

    # Cholesterol contribution
    risk += (num(panel.get("totalCholesterol"), 0) - 170) * 0.02

    # HDL contribution
    risk -= (num(panel.get("hdlC"), 0) - 50) * 0.03

    # Smoking
    if truthy(patient.get("smoker")):
        risk += 5

    # Diabetes
    if truthy(patient.get("diabetic")):
        risk += 3

    # Hypertension
    if truthy(patient.get("hypertensive")):
        risk += 2

    # Family history
    if truthy(patient.get("familyHistoryPrematureCAD")):
        risk += 2

    return max(0.0, min(100.0, risk))


def determine_risk_level(patient: dict, prevention_category: str) -> str:
    panel = _lipid_panel(patient)
    ldl_c = num(panel.get("ldlC"), 0)

    # Secondary prevention (ASCVD present)
    if prevention_category == "secondary":
        return "very-high"

    # High-risk conditions in primary prevention
    if prevention_category == "primary":
        # Severe hypercholesterolemia (LDL-C >= 190 mg/dL)
        if ldl_c >= 190:
            return "very-high"

        # Diabetes with additional risk factors
        if truthy(patient.get("diabetic")):
            if (
                num(patient.get("age"), 0) >= 40
                or truthy(patient.get("smoker"))
                or truthy(patient.get("hypertensive"))
            ):
                return "high"
            return "moderate"

        # 10-year ASCVD risk >= 7.5%
        ascvd_risk = calculate_ascvd_risk(patient)
        if ascvd_risk >= 7.5:
            return "high"

        # 10-year ASCVD risk 5-7.5%
        if ascvd_risk >= 5:
            return "moderate"

        return "low"

    # Primordial prevention
    return "low"


def determine_ldl_c_goal(risk_level: str) -> int:
    if risk_level == "very-high":
        return 55
    if risk_level == "high":
        return 70
    if risk_level == "moderate":
        return 100
    if risk_level == "low":
        return 130
    return 130


def determine_statin_intensity(risk_level: str, ldl_c: float, ldl_c_goal: float) -> str:
    if risk_level == "very-high":
        return "high"

    if risk_level == "high":
        return "high" if ldl_c > ldl_c_goal else "moderate"

    if risk_level == "moderate":
        return "moderate" if ldl_c > ldl_c_goal else "low"

    return "low" if ldl_c > ldl_c_goal else "none"


def get_statin_recommendation(intensity: str) -> str:
    if intensity == "high":
        return "High-intensity statin: Atorvastatin 40-80 mg daily or Rosuvastatin 20-40 mg daily"
    if intensity == "moderate":
        return (
            "Moderate-intensity statin: Atorvastatin 10-20 mg daily, "
            "Rosuvastatin 5-10 mg daily, or Simvastatin 20-40 mg daily"
        )
    if intensity == "low":
        return (
            "Low-intensity statin: Simvastatin 10 mg daily, "
            "Pravastatin 10-20 mg daily, or Lovastatin 20 mg daily"
        )
    return "Statin therapy not indicated at this time; focus on lifestyle modifications"


def recommend_non_statin_therapies(
    risk_level: str,
    ldl_c: float,
    ldl_c_goal: float,
    lpa: float | None = None,
) -> list[str]:
    therapies: list[str] = []

    # If LDL-C not at goal despite statin
    if ldl_c > ldl_c_goal:
        therapies.append("Ezetimibe 10 mg daily (reduces LDL-C by 15-20%)")

        if risk_level in ("very-high", "high"):
            therapies.append(
                "PCSK9 inhibitor (evolocumab, alirocumab, inclisiran) - reduces LDL-C by 40-60%"
            )
            therapies.append(
                "Bempedoic acid 120 mg daily (reduces LDL-C by 13-15%, uric acid lowering)"
            )

    # Elevated Lp(a) management
    if lpa is not None and truthy(lpa) and lpa > 50:
        therapies.append("Inclisiran (PCSK9i) - particularly effective for elevated Lp(a)")
        therapies.append(
            "Consider lipoprotein(a) apheresis if Lp(a) >200 nmol/L and very high risk"
        )

    # Elevated triglycerides
    if ldl_c <= ldl_c_goal and ldl_c > 0:
        # Calculate non-HDL-C
        non_hdl_c = ldl_c + (0 if ldl_c > 0 else 0)  # Simplified
        if non_hdl_c > ldl_c_goal + 30:
            therapies.append(
                "Icosapent ethyl 2-4 g daily (if triglycerides 135-499 mg/dL despite statin)"
            )
            therapies.append("GLP-1 receptor agonist (if diabetic or overweight)")

    return therapies


def _lpa_value(patient: dict) -> float | None:
    panel = _lipid_panel(patient)
    raw = panel.get("lpa")
    if raw is None:
        return None
    return num(raw, 0)


def assess(data: dict) -> dict:
    panel = _lipid_panel(data)
    ldl_c = num(panel.get("ldlC"), 0)
    lpa = _lpa_value(data)

    prevention_category = determine_prevention_category(data)
    risk_level = determine_risk_level(data, prevention_category)
    ldl_c_goal = determine_ldl_c_goal(risk_level)
    statin_intensity = determine_statin_intensity(risk_level, ldl_c, ldl_c_goal)
    statin_recommendation = get_statin_recommendation(statin_intensity)
    non_statin_therapies = recommend_non_statin_therapies(
        risk_level, ldl_c, ldl_c_goal, lpa
    )

    reasoning = ""

    if prevention_category == "secondary":
        reasoning = (
            "Patient has established ASCVD ("
            + ("prior MI, " if truthy(data.get("priorMI")) else "")
            + ("prior stroke, " if truthy(data.get("priorStroke")) else "")
            + ("prior PAD, " if truthy(data.get("priorPAD")) else "")
            + ("aortic aneurysm" if truthy(data.get("aorticAneurysm")) else "")
            + "). Very high-risk category with LDL-C goal <55 mg/dL."
        )
    elif prevention_category == "primary":
        if ldl_c >= 190:
            reasoning = (
                f"Severe hypercholesterolemia (LDL-C {_js_number(ldl_c)} mg/dL). "
                "Very high-risk category with LDL-C goal <55 mg/dL."
            )
        elif truthy(data.get("diabetic")):
            reasoning = (
                f"Diabetic patient with {risk_level} risk. "
                f"LDL-C goal <{ldl_c_goal} mg/dL."
            )
        else:
            ascvd_risk = calculate_ascvd_risk(data)
            reasoning = (
                f"Primary prevention with {risk_level} risk "
                f"(10-year ASCVD risk ~{_to_fixed(ascvd_risk, 1)}%). "
                f"LDL-C goal <{ldl_c_goal} mg/dL."
            )
    else:
        reasoning = (
            "Primordial prevention. Focus on lifestyle modifications and risk "
            f"factor reduction. LDL-C goal <{ldl_c_goal} mg/dL."
        )

    lipa_recommendation = None
    if lpa is not None and truthy(lpa) and lpa > 50:
        lipa_recommendation = (
            f"Elevated Lp(a) ({_js_number(lpa)} nmol/L). "
            "Consider PCSK9i or inclisiran for additional Lp(a) reduction."
        )

    if risk_level == "very-high":
        monitoring_interval = "4-12 weeks"
    elif risk_level == "high":
        monitoring_interval = "4-12 weeks"
    else:
        monitoring_interval = "3-6 months"

    return {
        "preventionCategory": prevention_category,
        "riskLevel": risk_level,
        "ldlCGoal": ldl_c_goal,
        "statinIntensity": statin_intensity,
        "statinRecommendation": statin_recommendation,
        "nonStatinTherapies": non_statin_therapies,
        "lipaRecommendation": lipa_recommendation,
        "monitoringInterval": monitoring_interval,
        "reasoning": reasoning,
    }


def _to_fixed(x: float, digits: int) -> str:
    """JS ``Number.prototype.toFixed`` — rounds half away from zero (Python's
    str/format uses banker's rounding, which can differ, e.g. 2.5 -> "2" vs
    JS "3"). Reproduce JS semantics explicitly."""
    factor = 10 ** digits
    scaled = x * factor
    rounded = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return f"{rounded / factor:.{digits}f}"


def present(native: dict) -> dict:
    """Card mapper override for two display fixes the generic mapper can't make:

    * ``ldlCGoal`` is a bare integer, so it rendered as "LDL C Goal: 70" with no
      units — the old UI showed "<70 mg/dL". Reformat it with the ``mg/dL`` unit.
    * ``monitoringInterval`` rendered alone, dropping the follow-up monitoring
      steps the old UI listed — fold both into a "Follow-up Monitoring" section.

    The ``assess()`` output is left untouched (engine contract / tests); the
    module's ``EVIDENCE`` list is attached by the registry after this returns.
    """
    card = build_card(native, logic_key=LOGIC_KEY)
    goal = native.get("ldlCGoal")
    interval = native.get("monitoringInterval")

    sections = []
    for sec in card["sections"]:
        sid = sec.get("id")
        if sid == "ldlcgoal" and goal is not None:
            sec = {
                "label": "LDL-C Treatment Goal",
                "type": "keyvalue",
                "items": [{"key": "Target LDL-C", "value": f"<{goal} mg/dL"}],
                "id": "ldlcgoal",
            }
        elif sid == "monitoringinterval":
            continue  # folded into the richer Follow-up Monitoring section below
        sections.append(sec)

    monitoring_items = _MONITORING_STEPS[:]
    if interval:
        monitoring_items = [f"Lipid panel recheck: {interval}"] + monitoring_items
    sections.append({
        "label": "Follow-up Monitoring",
        "type": "list",
        "items": monitoring_items,
        "id": "followupmonitoring",
    })

    card["sections"] = sections
    return card
