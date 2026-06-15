"""Spinal Cord Stimulator (SCS) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/scsLogic.ts (assessSCS).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num, truthy

LOGIC_KEY = "scs"

_ABSOLUTE_CONTRAINDICATIONS = [
    "active-infection",
    "coagulopathy",
    "demand-pacemaker",
    "psychosis",
    "drug-seeking",
    "pregnancy",
]

_HARD_CONTRA_LABELS = {
    "active-infection": "Active infection — must be resolved before implant",
    "coagulopathy": "Uncorrectable coagulopathy",
    "demand-pacemaker": "Demand cardiac pacemaker — absolute contraindication",
    "psychosis": "Untreated psychiatric disorder",
    "drug-seeking": "Active drug-seeking behavior",
    "pregnancy": "Pregnancy",
}


def assess(data: dict) -> dict:
    symptom_months = num(data.get("symptomDurationMonths"), 0)
    pain_score = num(data.get("painScore"), 0)
    trial_relief = num(data.get("trialReliefPercent"), 0)

    contraindications = data.get("contraindications") or []
    indications = data.get("indications") or []
    conservative_therapies = data.get("conservativeTherapies") or []
    psychological_clearance = truthy(data.get("psychologicalClearance"))
    prior_trial_success = truthy(data.get("priorTrialSuccess"))
    phase = data.get("phase")

    hard_contra = [c for c in contraindications if includes(_ABSOLUTE_CONTRAINDICATIONS, c)]

    if len(hard_contra) > 0:
        return {
            "recommendation": "SCS Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Absolute contraindications identified — SCS cannot proceed until resolved."],
            "contraindications": [_HARD_CONTRA_LABELS.get(c) or c for c in hard_contra],
            "optimizationSteps": [
                "Address all contraindications",
                "Psychiatric evaluation and treatment if needed",
            ],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    has_fbss = includes(indications, "fbss")
    has_crps = includes(indications, "crps")
    has_neuropathic_pain = includes(indications, "radiculopathy") or includes(
        indications, "diabetic-neuropathy"
    )
    adequate_conservative = len(conservative_therapies) >= 3

    if phase == "implant":
        if prior_trial_success and trial_relief >= 50 and psychological_clearance:
            cor, urgency = "I", "Appropriate"
            rationale.append("Successful SCS trial (≥50% pain relief) with psychological clearance")
            rationale.append("Permanent implant is strongly recommended per NANS/ASIPP guidelines")
        elif not prior_trial_success:
            cor, urgency = "III", "Trial Required First"
            rationale.append("Permanent implant requires successful trial period first")
            optimization_steps.append("Perform SCS trial before proceeding with permanent implant")
        elif trial_relief < 50:
            cor, urgency = "III", "Trial Unsuccessful"
            rationale.append("Trial relief <50% — permanent implant not recommended")
            optimization_steps.append("Consider alternative pain management strategies")
        elif not psychological_clearance:
            cor, urgency = "IIb", "Psychological Clearance Required"
            rationale.append("Psychological evaluation required before permanent implant")
            optimization_steps.append("Complete psychological evaluation with pain psychologist")
    elif phase == "trial":
        if (
            (has_fbss or has_crps or has_neuropathic_pain)
            and adequate_conservative
            and symptom_months >= 6
            and psychological_clearance
        ):
            cor, urgency = "I", "Appropriate"
            rationale.append(
                "Appropriate indication (FBSS, CRPS, or neuropathic pain) with adequate conservative therapy failure"
            )
            rationale.append("Psychological clearance obtained")
            rationale.append("SCS trial is strongly recommended per NANS guidelines")
        elif (
            (has_fbss or has_crps or has_neuropathic_pain)
            and adequate_conservative
            and not psychological_clearance
        ):
            cor, urgency = "IIa", "Psychological Clearance Needed"
            rationale.append("Appropriate indication with conservative therapy failure")
            optimization_steps.append("Complete psychological evaluation before trial")
        elif not adequate_conservative:
            cor, urgency = "IIb", "Insufficient Conservative Therapy"
            rationale.append(
                "Insufficient conservative therapy trial — most payers require ≥6 months multimodal treatment"
            )
            optimization_steps.append(
                "Continue multimodal therapy (PT, medications, injections, psychology) for ≥6 months"
            )
        else:
            cor, urgency = "IIb", "Insufficient Criteria"
            rationale.append("Indication or conservative therapy criteria not fully met")
            optimization_steps.append("Document specific indication (FBSS, CRPS, or neuropathic pain)")
    else:
        cor, urgency = "IIa", "Reasonable"
        rationale.append("SCS revision/replacement — appropriate if prior device provided benefit")
        optimization_steps.append("Document prior SCS benefit and reason for revision")

    if pain_score >= 7:
        rationale.append("Severe pain (NRS ≥7) supports intervention")
    if includes(contraindications, "mri-dependent"):
        optimization_steps.append("MRI-dependent condition — select MRI-compatible SCS device")

    if cor == "I":
        recommendation = (
            "Permanent SCS Implant Recommended"
            if phase == "implant"
            else "SCS Trial Recommended"
        )
    elif cor == "IIa":
        recommendation = "SCS Reasonable"
    elif cor == "III":
        recommendation = "SCS Not Indicated"
    else:
        recommendation = "Additional Requirements Needed"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if (has_fbss or has_crps) else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": [
            c for c in contraindications if not includes(_ABSOLUTE_CONTRAINDICATIONS, c)
        ],
        "optimizationSteps": optimization_steps,
    }
