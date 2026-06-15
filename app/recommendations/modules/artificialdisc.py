"""Artificial Disc Replacement (ADR) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/artificialDiscLogic.ts
(assessArtificialDisc).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, intnum, num

LOGIC_KEY = "artificialdisc"


def assess(data: dict) -> dict:
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)
    ndi = num(data.get("ndiScore") or "0", 0)
    levels = intnum(data.get("levels") or "1", 1)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active infection — absolute contraindication")
    if data.get("osteoporosis"):
        contraindications.append("Osteoporosis (T-score < -2.5) — contraindication for ADR")
    if data.get("instability"):
        contraindications.append("Spinal instability — ADR contraindicated; fusion preferred")
    if data.get("facetArthrosis"):
        contraindications.append("Significant facet arthrosis at affected level — contraindication for ADR")
    if levels > 2:
        contraindications.append("More than 2 levels — exceeds FDA indication for most devices")
    if data.get("medicallyUnfit"):
        contraindications.append("Medically unfit for surgery")

    if contraindications:
        return {
            "recommendation": "Artificial Disc Replacement Contraindicated",
            "cor": "III",
            "loe": "B",
            "urgency": "Contraindicated",
            "rationale": ["One or more contraindications identified. Consider fusion instead."],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Consider spinal fusion as alternative",
                "Bone density scan to rule out osteoporosis",
                "Evaluate facet joint status on CT",
            ],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    imaging_findings = data.get("imagingFindings") or []

    if conserv_months >= 6 and ndi >= 30 and includes(imaging_findings, "disc-herniation"):
        cor, urgency = "I", "Appropriate"
        rationale.append("DDD with radiculopathy, adequate conservative therapy failure, and no contraindications")
        rationale.append("FDA-approved device available for this indication")
        rationale.append("ADR preserves motion segment and may reduce adjacent segment disease vs. fusion")
    elif conserv_months >= 6 and ndi >= 20:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("Adequate conservative therapy failure with functional impairment")
        rationale.append("ADR is a reasonable alternative to fusion in appropriate candidates")
    else:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Conservative therapy trial insufficient or criteria not fully met")
        optimization_steps.append("Continue PT, medications, and injections for ≥6 months")
        optimization_steps.append("Complete NDI functional assessment")

    if cor == "I":
        recommendation = "ADR Recommended"
    elif cor == "IIa":
        recommendation = "ADR Reasonable"
    else:
        recommendation = "ADR — Additional Criteria Needed"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
