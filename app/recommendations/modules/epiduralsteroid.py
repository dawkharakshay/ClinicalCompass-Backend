"""Epidural Steroid Injection (ESI) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/epiduralSteroidLogic.ts
(assessEpiduralSteroid).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, intnum, num

LOGIC_KEY = "epiduralsteroid"


def assess(data: dict) -> dict:
    conserv_weeks = num(data.get("conservativeTherapyWeeks"), 0)
    pain_score = num(data.get("painScore"), 0)
    prior_count = intnum(data.get("priorInjectionCount"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active infection — absolute contraindication")
    if data.get("coagulopathy"):
        contraindications.append(
            "Uncorrected coagulopathy — hold anticoagulation per guidelines before proceeding"
        )
    if data.get("allergy"):
        contraindications.append(
            "Allergy to steroids or contrast — use alternative agents or consider desensitization"
        )

    if contraindications:
        return {
            "recommendation": "ESI Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Contraindications identified — address before proceeding."],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Bridge anticoagulation per procedural guidelines",
                "Allergy evaluation if steroid/contrast allergy",
            ],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    symptoms = data.get("symptoms") or []
    imaging_findings = data.get("imagingFindings") or []

    has_radicular = includes(symptoms, "radicular-pain")
    has_neurogenic_claudication = includes(symptoms, "neurogenic-claudication")
    has_disc_herniation = includes(imaging_findings, "disc-herniation")
    has_stenosis = includes(imaging_findings, "central-stenosis") or includes(
        imaging_findings, "foraminal-stenosis"
    )

    if prior_count >= 3:
        cor, urgency = "IIb", "Frequency Limit Reached"
        rationale.append("Most payers limit ESI to 3 injections per region per year")
        rationale.append("Consider alternative interventions: RFA, surgery, or pain psychology")
        optimization_steps.append("Evaluate for surgical candidacy if not already done")
        optimization_steps.append("Consider radiofrequency ablation for facetogenic component")
    elif has_radicular and has_disc_herniation and conserv_weeks >= 4:
        cor, urgency = "I", "Appropriate"
        rationale.append(
            "Radicular pain with imaging-confirmed disc herniation and nerve root compression"
        )
        rationale.append("Conservative therapy trial completed (≥4 weeks)")
        rationale.append("ESI provides short-term pain relief and may facilitate PT participation")
    elif (has_neurogenic_claudication or has_radicular) and has_stenosis and conserv_weeks >= 4:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("Neurogenic claudication or radiculopathy with stenosis")
        rationale.append("ESI is reasonable for short-term symptom relief")
    elif conserv_weeks < 4:
        cor, urgency = "IIb", "Continue Conservative Therapy"
        rationale.append("Conservative therapy trial insufficient — continue for ≥4 weeks")
        optimization_steps.append(
            "Continue PT, NSAIDs, and activity modification for ≥4 weeks"
        )
    else:
        cor, urgency = "IIb", "Insufficient Criteria"
        rationale.append("Radicular symptoms or imaging correlation not clearly documented")
        optimization_steps.append("Obtain MRI to confirm nerve root compression")
        optimization_steps.append("Document dermatomal distribution of symptoms")

    if data.get("priorInjectionResponse") == "good":
        rationale.append("Prior ESI response was good — repeat injection is appropriate")
    if data.get("priorInjectionResponse") == "none":
        optimization_steps.append(
            "Prior ESI had no response — reconsider diagnosis and approach; "
            "consider transforaminal vs. interlaminar"
        )
    if pain_score >= 8:
        rationale.append(
            "Severe pain (NRS ≥8) supports intervention to facilitate PT participation"
        )

    if cor == "I":
        recommendation = "ESI Recommended"
    elif cor == "IIa":
        recommendation = "ESI Reasonable"
    elif urgency == "Frequency Limit Reached":
        recommendation = "Frequency Limit — Consider Alternatives"
    else:
        recommendation = "Continue Conservative Therapy"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if has_disc_herniation else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
