"""Total Hip Arthroplasty (THA) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/thaLogic.ts (assessTHA).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, intnum, num

LOGIC_KEY = "tha"

_COR_RECOMMENDATION = {"I": "THA Recommended", "IIa": "THA Reasonable"}


def assess(data: dict) -> dict:
    bmi = num(data.get("bmi"), 0)
    harris_pain = num(data.get("harrisPainScore") or "0", 44)
    kl = intnum(data.get("kellgrenLawrence") or "0", 0)
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active systemic infection — absolute contraindication")
    if data.get("activeHipInfection"):
        contraindications.append("Active hip joint infection — absolute contraindication")
    if data.get("severeVascularDisease"):
        contraindications.append("Severe peripheral vascular disease — high surgical risk")
    if data.get("medicallyUnfit"):
        contraindications.append("Medically unfit for surgery — requires optimization")

    if contraindications:
        return {
            "recommendation": "THA Contraindicated or Requires Optimization",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["One or more absolute or relative contraindications identified."],
            "contraindications": contraindications,
            "optimizationSteps": ["Address contraindications before proceeding with THA"],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    if data.get("avascularNecrosis"):
        cor, urgency = "I", "Appropriate"
        rationale.append("Avascular necrosis of the femoral head — THA is the definitive treatment for advanced AVN")
        rationale.append("Earlier intervention improves outcomes by preventing femoral head collapse")
    elif kl >= 3 and harris_pain <= 20 and conserv_months >= 3:
        cor, urgency = "I", "Appropriate"
        rationale.append("Severe hip OA (KL ≥3) with significant pain and functional limitation")
        rationale.append("Harris Hip Score pain component indicates severe disability")
        rationale.append("Conservative therapy trial completed")
    elif kl >= 2 and harris_pain <= 30 and conserv_months >= 3:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("Moderate hip OA with meaningful pain and functional limitation")
        rationale.append("THA is a reasonable option after shared decision-making")
    else:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Criteria for THA not fully met — continue conservative management")
        optimization_steps.append("Continue PT, weight management, and analgesics for ≥3 months")
        optimization_steps.append("Consider intraarticular corticosteroid injection")

    if bmi > 40:
        optimization_steps.append("BMI >40: weight loss recommended before elective THA")
    comorbidities = data.get("comorbidities") or []
    if includes(comorbidities, "diabetes"):
        optimization_steps.append("Optimize glycemic control (HbA1c <8%)")
    if includes(comorbidities, "smoking"):
        optimization_steps.append("Smoking cessation ≥4 weeks before surgery")

    return {
        "recommendation": _COR_RECOMMENDATION.get(cor, "THA — Additional Criteria Needed"),
        "cor": cor,
        "loe": "A" if kl >= 3 else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
