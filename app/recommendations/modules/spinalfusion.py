"""Spinal Fusion Clinical Compass appropriateness.

Ported 1:1 from old_static_code/client/src/lib/spinalFusionLogic.ts
(assessSpinalFusion).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num

LOGIC_KEY = "spinalfusion"


def assess(data: dict) -> dict:
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)
    odi = num(data.get("odiScore") or "0", 0)
    ndi = num(data.get("ndiScore") or "0", 0)
    pain_score = num(data.get("painScore"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active infection — absolute contraindication")
    if data.get("severeOsteoporosis"):
        contraindications.append(
            "Severe osteoporosis — high risk of hardware failure; requires optimization"
        )
    if data.get("medicallyUnfit"):
        contraindications.append("Medically unfit for surgery")

    if contraindications:
        return {
            "recommendation": "Spinal Fusion Contraindicated or Requires Optimization",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Contraindications identified — address before proceeding."],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Address all contraindications",
                "Bone density optimization if osteoporosis present",
            ],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    if data.get("progressiveNeurologicDeficit") or data.get("myelopathy"):
        cor, urgency = "I", "Urgent"
        rationale.append(
            "Progressive neurologic deficit or myelopathy — urgent surgical evaluation required"
        )
        rationale.append("Delay in treatment risks permanent neurologic injury")
    elif data.get("instability") and conserv_months >= 6 and (odi >= 40 or ndi >= 30):
        cor, urgency = "I", "Appropriate"
        rationale.append("Documented spinal instability with significant functional impairment")
        rationale.append("Adequate conservative therapy trial completed")
        rationale.append("Functional assessment scores support surgical intervention")
    elif conserv_months >= 6 and (odi >= 40 or ndi >= 30) and pain_score >= 6:
        cor, urgency = "IIa", "Reasonable"
        rationale.append(
            "Significant functional impairment with adequate conservative therapy failure"
        )
        rationale.append("Fusion is reasonable after shared decision-making")
    elif conserv_months < 6:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Conservative therapy trial insufficient — continue for ≥6 months")
        optimization_steps.append(
            "Continue PT, medications, and injections for ≥6 months total"
        )
        optimization_steps.append("Document functional scores at each visit (ODI or NDI)")
    else:
        cor, urgency = "IIb", "Insufficient Criteria"
        rationale.append("Functional impairment criteria not fully met")
        optimization_steps.append(
            "Complete ODI (lumbar) or NDI (cervical) functional assessment"
        )
        optimization_steps.append("Document pain scores at multiple visits")

    symptoms = data.get("symptoms") or []
    if includes(symptoms, "smoking"):
        optimization_steps.append(
            "Smoking cessation required — significantly impairs fusion rates"
        )
    if includes(symptoms, "diabetes"):
        optimization_steps.append("Optimize glycemic control (HbA1c <8%)")

    if cor == "I":
        recommendation = "Spinal Fusion Recommended"
    elif cor == "IIa":
        recommendation = "Spinal Fusion Reasonable"
    else:
        recommendation = "Spinal Fusion — Additional Criteria Needed"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if data.get("instability") else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
