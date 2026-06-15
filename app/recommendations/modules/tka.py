"""Total Knee Arthroplasty (TKA) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/tkaLogic.ts (assessTKA).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, intnum, num

LOGIC_KEY = "tka"


def assess(data: dict) -> dict:
    age = num(data.get("age"), 0)
    bmi = num(data.get("bmi"), 0)
    koos_pain = num(data.get("koosPainScore"), 100)
    koos_adl = num(data.get("koosADLScore"), 100)
    kl = intnum(data.get("klGrade") or data.get("kellgrenLawrence"), 0)
    _pain_score = num(data.get("painScore"), 0)  # parsed in TS; unused downstream
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active systemic infection — absolute contraindication")
    if data.get("activeKneeInfection"):
        contraindications.append("Active knee joint infection — absolute contraindication")
    if data.get("severeVascularDisease"):
        contraindications.append("Severe peripheral vascular disease — high surgical risk")
    if data.get("medicallyUnfit"):
        contraindications.append("Medically unfit for surgery — requires optimization")

    if contraindications:
        return {
            "recommendation": "TKA Contraindicated or Requires Optimization",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": [
                "One or more absolute or relative contraindications identified. Address before proceeding."
            ],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Obtain infectious disease clearance if infection present",
                "Vascular surgery consultation for PVD",
                "Medical optimization for surgical fitness",
            ],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    if kl >= 3 and koos_pain <= 45 and koos_adl <= 45 and conserv_months >= 3:
        cor, urgency = "I", "Appropriate"
        rationale.append(
            "Radiographic evidence of moderate-severe OA (KL ≥3) with significant functional impairment"
        )
        rationale.append("KOOS pain and ADL scores indicate substantial disability")
        rationale.append("Conservative therapy trial completed")
        rationale.append("TKA is strongly recommended per AAOS guidelines")
    elif kl >= 2 and koos_pain <= 55 and conserv_months >= 3:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("Moderate OA with meaningful pain and functional limitation")
        rationale.append("Adequate conservative therapy trial documented")
        rationale.append("TKA is a reasonable option per shared decision-making")
    elif kl >= 2 and conserv_months < 3:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append(
            "OA severity supports eventual TKA but conservative therapy trial is insufficient"
        )
        optimization_steps.append(
            "Continue physical therapy, weight management, and analgesics for ≥3 months"
        )
        optimization_steps.append(
            "Consider intraarticular corticosteroid or hyaluronic acid injection"
        )
    else:
        cor, urgency = "IIb", "Insufficient Criteria"
        rationale.append("Radiographic or functional criteria for TKA not yet met")
        optimization_steps.append("Repeat weight-bearing X-rays with KL grading")
        optimization_steps.append("Complete KOOS functional assessment")
        optimization_steps.append("Ensure adequate conservative therapy trial (≥3 months)")

    if bmi > 40:
        optimization_steps.append(
            "BMI >40: weight loss to <40 recommended before elective TKA to reduce complication risk"
        )
    if age < 55:
        optimization_steps.append(
            "Age <55: discuss implant longevity and potential need for revision surgery"
        )
    comorbidities = data.get("comorbidities") or []
    if includes(comorbidities, "diabetes"):
        optimization_steps.append("Optimize glycemic control (HbA1c <8%) before surgery")
    if includes(comorbidities, "smoking"):
        optimization_steps.append("Smoking cessation ≥4 weeks before surgery")

    if cor == "I":
        recommendation = "TKA Recommended"
    elif cor == "IIa":
        recommendation = "TKA Reasonable"
    else:
        recommendation = "TKA — Additional Criteria Needed"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if kl >= 3 else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
