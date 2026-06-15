"""Facet Joint Injection appropriateness.

Ported 1:1 from old_static_code/client/src/lib/facetJointLogic.ts
(assessFacetJoint).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, intnum, num

LOGIC_KEY = "facetjoint"


def assess(data: dict) -> dict:
    conserv_months = num(data.get("conservativeTherapyMonths"), 0)
    pain_score = num(data.get("painScore"), 0)
    prior_count = intnum(data.get("priorFacetCount"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active infection — absolute contraindication")
    if data.get("coagulopathy"):
        contraindications.append("Uncorrected coagulopathy — hold anticoagulation per guidelines")
    if data.get("allergy"):
        contraindications.append("Allergy to steroids or contrast")

    if contraindications:
        return {
            "recommendation": "Facet Injection Contraindicated",
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

    symptoms = data.get("symptoms") or []
    has_axial_pain = includes(symptoms, "axial-pain")
    has_pain_extension = includes(symptoms, "pain-extension")
    has_no_neurologic = includes(symptoms, "no-neurologic")

    if prior_count >= 3:
        cor = "IIb"
        urgency = "Frequency Limit Reached"
        rationale.append("Most payers limit facet injections to 3 per region per year")
        optimization_steps.append("Consider medial branch block followed by RFA if not already done")
        optimization_steps.append("Evaluate for other pain generators")
    elif data.get("procedureType") == "medial-branch-block" and data.get("diagnosticBlockPositive"):
        cor = "I"
        urgency = "Appropriate"
        rationale.append("Positive prior diagnostic block (≥80% relief) — confirmatory MBB or RFA is appropriate")
        rationale.append("Two positive diagnostic blocks are required before RFA authorization by most payers")
    elif has_axial_pain and has_pain_extension and has_no_neurologic and conserv_months >= 3:
        cor = "IIa"
        urgency = "Reasonable"
        rationale.append("Axial spine pain with extension-related pattern and no significant neurologic deficit")
        rationale.append("Clinical pattern consistent with facetogenic pain")
        rationale.append("Conservative therapy trial completed")
    elif conserv_months < 3:
        cor = "IIb"
        urgency = "Continue Conservative Therapy"
        rationale.append("Conservative therapy trial insufficient")
        optimization_steps.append("Continue PT and analgesics for ≥3 months")
    else:
        cor = "IIb"
        urgency = "Insufficient Criteria"
        rationale.append("Clinical criteria for facetogenic pain not clearly met")
        optimization_steps.append("Document axial pain pattern, extension provocation, and absence of radicular symptoms")

    if pain_score >= 7:
        rationale.append("Severe pain (NRS ≥7) supports intervention")
    if data.get("priorFacetResponse") == "good":
        rationale.append("Prior facet injection response was good — repeat injection appropriate")

    if cor == "I":
        recommendation = "Facet Injection / MBB Recommended"
    elif cor == "IIa":
        recommendation = "Facet Injection Reasonable"
    else:
        recommendation = "Continue Conservative Therapy"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
