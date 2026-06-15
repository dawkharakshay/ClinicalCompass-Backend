"""Radiofrequency Ablation (RFA) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/rfaLogic.ts (assessRFA).
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num

LOGIC_KEY = "rfa"


def assess(data: dict) -> dict:
    block1 = num(data.get("diagnosticBlock1Relief"), 0)
    block2 = num(data.get("diagnosticBlock2Relief"), 0)
    symptom_months = num(data.get("symptomDurationMonths"), 0)
    pain_score = num(data.get("painScore"), 0)

    contraindications: list[str] = []
    if data.get("activeInfection"):
        contraindications.append("Active infection — absolute contraindication")
    if data.get("coagulopathy"):
        contraindications.append("Uncorrected coagulopathy")
    if data.get("allergy"):
        contraindications.append("Allergy to local anesthetic or contrast")
    if data.get("pregnancy"):
        contraindications.append("Pregnancy — avoid fluoroscopy")
    if data.get("pacemaker"):
        contraindications.append(
            "Pacemaker/ICD — relative contraindication; use bipolar technique; "
            "cardiology consultation"
        )

    hard_contraindications = [
        c
        for c in contraindications
        if not includes(c, "relative") and not includes(c, "Pacemaker")
    ]
    if len(hard_contraindications) > 0:
        return {
            "recommendation": "RFA Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Absolute contraindications identified."],
            "contraindications": contraindications,
            "optimizationSteps": [],
        }

    rationale: list[str] = []
    optimization_steps: list[str] = []
    cor = "IIb"
    urgency = "Elective"

    both_blocks_positive = block1 >= 80 and block2 >= 80
    one_block_positive = (block1 >= 80 or block2 >= 80) and not (
        block1 >= 80 and block2 >= 80
    )

    if both_blocks_positive and symptom_months >= 3:
        cor, urgency = "I", "Appropriate"
        rationale.append(
            "Two positive diagnostic medial branch blocks (≥80% relief each) — "
            "gold standard for RFA candidacy"
        )
        rationale.append(
            "Chronic pain (≥3 months) with facetogenic source confirmed"
        )
        rationale.append("RFA is strongly recommended per ASIPP guidelines")
    elif one_block_positive and symptom_months >= 3:
        cor, urgency = "IIa", "Reasonable"
        rationale.append(
            "One positive diagnostic block — second confirmatory block "
            "recommended before RFA"
        )
        rationale.append(
            "Some payers accept single block with ≥80% relief; verify payer policy"
        )
        optimization_steps.append(
            "Perform second diagnostic medial branch block to confirm "
            "facetogenic source"
        )
    elif block1 < 80 and block2 < 80 and (block1 > 0 or block2 > 0):
        cor, urgency = "III", "Not Indicated"
        rationale.append(
            "Diagnostic blocks did not achieve ≥80% relief — facetogenic "
            "source not confirmed"
        )
        rationale.append("RFA is not indicated without positive diagnostic blocks")
        optimization_steps.append(
            "Re-evaluate pain generator — consider discogenic, sacroiliac, or "
            "myofascial sources"
        )
        optimization_steps.append(
            "Consider alternative interventions: ESI, SI joint injection, or "
            "pain psychology"
        )
    else:
        cor, urgency = "IIb", "Diagnostic Blocks Required"
        rationale.append(
            "Diagnostic medial branch blocks have not been performed or results "
            "not entered"
        )
        optimization_steps.append(
            "Perform two diagnostic medial branch blocks before proceeding with RFA"
        )
        optimization_steps.append("Document ≥80% pain relief from each block")

    if pain_score >= 7:
        rationale.append("Severe pain (NRS ≥7) supports intervention")
    if data.get("pacemaker"):
        optimization_steps.append(
            "Pacemaker present — use bipolar RFA technique; obtain cardiology "
            "clearance"
        )

    if cor == "I":
        recommendation = "RFA Recommended"
    elif cor == "IIa":
        recommendation = "RFA Reasonable (Second Block Needed)"
    elif cor == "III":
        recommendation = "RFA Not Indicated"
    else:
        recommendation = "Diagnostic Blocks Required First"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if both_blocks_positive else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
    }
