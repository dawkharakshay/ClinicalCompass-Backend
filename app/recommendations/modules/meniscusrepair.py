"""Meniscus Repair appropriateness.

Ported 1:1 from old_static_code/client/src/lib/meniscusRepairLogic.ts
(assessMeniscusRepair).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num

LOGIC_KEY = "meniscusrepair"


def assess(data: dict) -> dict:
    # parseFloat(...) || 0 — both NaN and 0 fall back to 0 (matches `num`).
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)
    age = num(data.get("age"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active knee infection — absolute contraindication")
    if data.get("severeOA"):
        contraindications.append(
            "Severe knee osteoarthritis (bone-on-bone) — meniscectomy/repair unlikely to benefit; consider TKA"
        )

    if contraindications:
        return {
            "recommendation": "Knee Arthroscopy Contraindicated",
            "cor": "III",
            "loe": "B",
            "urgency": "Contraindicated",
            "rationale": ["Contraindications identified."],
            "contraindications": contraindications,
            "optimizationSteps": [],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    symptoms = data.get("symptoms") or []
    tear_characteristics = data.get("tearCharacteristics") or []

    is_mechanical = includes(symptoms, "locking") or includes(symptoms, "giving-way")
    is_peripheral = includes(tear_characteristics, "peripheral-zone")
    is_bucket_handle = data.get("tearPattern") == "bucket-handle"
    is_complex = data.get("tearPattern") == "complex"

    if is_bucket_handle and is_mechanical:
        cor, urgency = "I", "Urgent"
        rationale.append(
            "Locked bucket-handle tear with mechanical symptoms — urgent arthroscopic intervention recommended"
        )
        rationale.append("Delay risks irreversible cartilage damage from locked fragment")
    elif is_mechanical and not is_complex and not data.get("osteoarthritis"):
        cor, urgency = "I", "Appropriate"
        rationale.append("Mechanical symptoms (locking/giving way) with repairable tear pattern")
        rationale.append("Arthroscopic repair or meniscectomy recommended")
        if is_peripheral and age < 50:
            rationale.append(
                "Peripheral (vascular) zone tear in younger patient — repair preferred over meniscectomy"
            )
    elif is_complex or data.get("osteoarthritis"):
        cor, urgency = "IIb", "Limited Benefit Expected"
        rationale.append(
            "Complex/degenerative tear or concurrent OA — evidence does not support arthroscopy over PT"
        )
        rationale.append(
            "AAOS and NEJM trials show no benefit of arthroscopy over PT for degenerative tears with OA"
        )
        optimization_steps.append("Continue PT and weight management as first-line treatment")
        optimization_steps.append("Consider intraarticular injection for symptom relief")
    elif conserv_months < 3 and not is_mechanical:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Non-mechanical tear without adequate conservative therapy trial")
        optimization_steps.append("Continue PT for ≥3 months before considering surgery")
    else:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("Symptomatic meniscal tear with adequate conservative therapy failure")
        rationale.append("Arthroscopy is reasonable in appropriate candidates")

    if data.get("activeSports") and is_peripheral:
        optimization_steps.append(
            "Active athlete with peripheral tear — repair preferred to preserve meniscal function"
        )

    if cor == "I":
        recommendation = "Knee Arthroscopy Recommended"
    elif cor == "IIa":
        recommendation = "Arthroscopy Reasonable"
    elif cor == "IIb" and urgency == "Urgent":
        recommendation = "Urgent Arthroscopy"
    else:
        recommendation = "Continue Conservative Therapy"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if is_bucket_handle else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
