"""Sclerotherapy (Foam & Liquid) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/sclerotherapyLogic.ts
(assessSclerotherapy).

Based on: SVS/AVF 2022 Clinical Practice Guidelines for Chronic Venous
Disease; European Guidelines on Sclerotherapy (Rabe E, et al. Phlebology.
2014); Gloviczki P, et al. J Vasc Surg Venous Lymphat Disord. 2023.
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, num, parse_float

LOGIC_KEY = "sclerotherapy"


def assess(data: dict) -> dict:
    contraindications: list[str] = []
    rationale: list[str] = []
    optimization_steps: list[str] = []
    foam_warnings: list[str] = []

    # Absolute contraindications
    if data.get("pregnancy"):
        contraindications.append(
            "Pregnancy — defer sclerotherapy until postpartum (Category X for most sclerosants)"
        )
    if data.get("activeInfection"):
        contraindications.append(
            "Active infection at injection site — treat before proceeding"
        )
    if data.get("allergyToSclerosant"):
        contraindications.append(
            "Known allergy to sclerosant agent — use alternative agent or refer to allergy"
        )
    if data.get("severePeripheralArterialDisease"):
        contraindications.append(
            "Severe peripheral arterial disease (ABI <0.5) — sclerotherapy may worsen limb perfusion"
        )
    if data.get("immobility"):
        contraindications.append(
            "Immobile patient — high DVT risk post-sclerotherapy; address mobility first"
        )

    if len(contraindications) > 0:
        return {
            "recommendation": "Sclerotherapy Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": [
                "Absolute contraindication(s) identified — address before proceeding."
            ],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Resolve contraindication(s) before reassessing candidacy"
            ],
            "foamWarnings": [],
            "agentRecommendation": "",
        }

    # Foam-specific relative contraindications
    if data.get("foamRequested") or parse_float(data.get("vesselDiameter")) >= 3:
        if data.get("patentForamenOvale"):
            foam_warnings.append(
                "Patent foramen ovale (PFO): Foam sclerotherapy carries risk of paradoxical embolism — use liquid sclerosant or consult cardiology"
            )
        if data.get("migraineWithAura"):
            foam_warnings.append(
                "Migraine with aura: Relative contraindication to foam — consider liquid sclerotherapy; foam may trigger neurological events via microemboli"
            )
        if data.get("breastfeeding"):
            foam_warnings.append(
                "Breastfeeding: Pause breastfeeding for 24–48 hours after foam sclerotherapy"
            )
        if data.get("knownDVT"):
            foam_warnings.append(
                "Prior DVT: Obtain duplex to confirm absence of residual thrombus; anticoagulation may be needed peri-procedure"
            )

    ceap_class = data.get("ceapClass") or ""
    ceap_num = intnum(str(ceap_class).replace("C", "", 1), 0)
    vessel_diameter = num(data.get("vesselDiameter"), 0)
    compression_weeks = num(data.get("compressionWeeks"), 0)

    cor = "IIb"
    urgency = "Elective"

    vessel_type = data.get("vesselType")
    prior_ablation = data.get("priorAblation")
    truncal_reflux = data.get("truncalReflux")

    # Truncal reflux should be treated first
    if truncal_reflux and not prior_ablation:
        cor = "IIb"
        urgency = "Truncal Reflux — Ablation First"
        rationale.append(
            "Duplex-confirmed truncal (GSV/SSV) reflux is present — endovenous ablation should be performed before sclerotherapy to address the source of reflux"
        )
        rationale.append(
            "Sclerotherapy of varicosities without treating the source has high recurrence rates"
        )
        optimization_steps.append(
            "Refer for endovenous thermal ablation (EVLA or RFA) of the incompetent truncal vein first"
        )
        optimization_steps.append(
            "Sclerotherapy of residual varicosities can be performed 4–8 weeks post-ablation"
        )
    elif ceap_num == 1 and (
        vessel_type == "telangiectasia" or vessel_type == "reticular"
    ):
        # C1 — telangiectasias and reticular veins: sclerotherapy is first-line
        cor = "I"
        urgency = "Appropriate"
        rationale.append(
            "CEAP C1 (telangiectasias/reticular veins) — sclerotherapy is the first-line treatment"
        )
        rationale.append(
            "SVS 2022: Liquid sclerotherapy recommended for telangiectasias; foam for reticular veins ≥1 mm"
        )
        if vessel_diameter < 1:
            rationale.append(
                "Vessel diameter <1 mm: Fine-needle liquid sclerotherapy (polidocanol 0.25–0.5% or STS 0.1–0.25%)"
            )
        elif vessel_diameter >= 1 and vessel_diameter < 3:
            rationale.append(
                "Vessel diameter 1–3 mm: Liquid or foam sclerotherapy appropriate (polidocanol 0.5–1% or STS 0.25–0.5%)"
            )
    elif ceap_num >= 2 and (prior_ablation or not truncal_reflux):
        # C2+ residual varicosities after ablation or isolated varicosities without truncal reflux
        cor = "I"
        urgency = "Appropriate"
        rationale.append(
            f"CEAP {ceap_class} — "
            + (
                "residual varicosities after prior ablation"
                if prior_ablation
                else "isolated varicosities without truncal reflux"
            )
        )
        rationale.append(
            "SVS 2022: Foam sclerotherapy is recommended for varicosities 3–6 mm in diameter"
        )
        if vessel_diameter >= 6:
            rationale.append(
                "Large varicosities (≥6 mm): Consider ambulatory phlebectomy as alternative to foam sclerotherapy"
            )
            optimization_steps.append(
                "Ambulatory phlebectomy may be more effective for large varicosities ≥6 mm"
            )
    elif compression_weeks < 3 and ceap_num >= 2:
        cor = "IIb"
        urgency = "Continue Compression Therapy"
        rationale.append(
            "Compression therapy trial insufficient — most payers require ≥3–6 weeks for CEAP C2+"
        )
        optimization_steps.append(
            "Continue graduated compression stockings (20–30 mmHg) for ≥6 weeks"
        )
        optimization_steps.append(
            "Document compliance and symptom response before requesting authorization"
        )
    else:
        cor = "IIb"
        urgency = "Insufficient Criteria"
        optimization_steps.append(
            "Document CEAP classification with duplex ultrasound findings"
        )
        optimization_steps.append(
            "Complete compression stocking trial ≥6 weeks for CEAP C2+"
        )

    # Agent recommendation
    agent_recommendation = ""
    if vessel_diameter < 1:
        agent_recommendation = (
            "Liquid sclerotherapy: Polidocanol 0.25–0.5% or STS 0.1–0.25% (fine-needle technique)"
        )
    elif vessel_diameter >= 1 and vessel_diameter < 3:
        agent_recommendation = "Liquid or foam: Polidocanol 0.5–1% or STS 0.25–0.5%"
    elif vessel_diameter >= 3 and vessel_diameter < 6:
        agent_recommendation = (
            "Foam sclerotherapy: Polidocanol 1–3% or STS 1–3% (Tessari method, 1:4 liquid:air ratio)"
        )
    elif vessel_diameter >= 6:
        agent_recommendation = (
            "Foam sclerotherapy or ambulatory phlebectomy: Polidocanol 3% foam; consider phlebectomy for veins ≥6 mm"
        )

    if cor == "I":
        recommendation = "Sclerotherapy Recommended"
    elif urgency == "Truncal Reflux — Ablation First":
        recommendation = (
            "Treat Truncal Reflux First — Ablation Recommended Before Sclerotherapy"
        )
    elif urgency == "Continue Compression Therapy":
        recommendation = "Continue Compression Therapy — Sclerotherapy Premature"
    else:
        recommendation = "Insufficient Criteria for Sclerotherapy"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if ceap_num >= 2 else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
        "foamWarnings": foam_warnings,
        "agentRecommendation": agent_recommendation,
    }
