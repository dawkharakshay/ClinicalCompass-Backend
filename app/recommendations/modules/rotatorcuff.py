"""Rotator Cuff Repair appropriateness.

Ported 1:1 from old_static_code/client/src/lib/rotatorCuffLogic.ts
(assessRotatorCuff).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num

LOGIC_KEY = "rotatorcuff"


def assess(data: dict) -> dict:
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)
    pain_score = num(data.get("painScore"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active shoulder infection — absolute contraindication")
    if data.get("severeGlenohumeralArthritis"):
        contraindications.append("Severe glenohumeral arthritis — consider shoulder arthroplasty instead")

    if contraindications:
        return {
            "recommendation": "Arthroscopic Repair Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Contraindications identified."],
            "contraindications": contraindications,
            "optimizationSteps": [],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    tear_characteristics = data.get("tearCharacteristics") or []
    tear_size = data.get("tearSize")
    is_full_thickness = includes(tear_characteristics, "full-thickness")
    is_large_or_massive = tear_size == "large" or tear_size == "massive"
    has_retraction = includes(tear_characteristics, "retraction")
    has_atrophy = includes(tear_characteristics, "muscle-atrophy")

    if data.get("acuteTear") and is_full_thickness:
        cor, urgency = "I", "Urgent"
        rationale.append(
            "Acute full-thickness rotator cuff tear — early repair (within 6 weeks) strongly recommended"
        )
        rationale.append("Delayed repair risks irreversible muscle atrophy and retraction")
    elif is_full_thickness and conserv_months >= 3 and pain_score >= 6:
        cor, urgency = "I", "Appropriate"
        rationale.append(
            "Full-thickness tear with persistent pain and functional limitation after conservative therapy"
        )
        rationale.append("Surgical repair recommended per AAOS guidelines")
    elif is_large_or_massive:
        cor, urgency = "IIa", "Appropriate"
        rationale.append("Large or massive tear — surgical repair or debridement recommended")
        if has_retraction or has_atrophy:
            optimization_steps.append(
                "Significant retraction/atrophy noted — repair may be technically challenging; "
                "consider tendon transfer"
            )
    elif conserv_months < 3 and not data.get("acuteTear"):
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Conservative therapy trial insufficient — continue for ≥3 months")
        optimization_steps.append(
            "Continue PT focusing on rotator cuff strengthening and scapular stabilization"
        )
        optimization_steps.append("Consider subacromial corticosteroid injection")
    else:
        cor, urgency = "IIa", "Reasonable"
        rationale.append(
            "Rotator cuff repair is reasonable given tear characteristics and clinical presentation"
        )

    if data.get("dominantArm"):
        rationale.append("Dominant arm affected — functional impact supports surgical intervention")
    if data.get("highDemandActivity"):
        rationale.append("High-demand overhead activity — repair supports return to activity")

    if cor == "I":
        recommendation = "Rotator Cuff Repair Recommended"
    elif cor == "IIa":
        recommendation = "Repair Reasonable"
    else:
        recommendation = "Continue Conservative Therapy"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if is_full_thickness else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
