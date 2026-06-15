"""Endovenous Ablation (Laser/Radiofrequency) appropriateness.

Ported 1:1 from old_static_code/client/src/lib/endovenousAblationLogic.ts
(assessEndovenousAblation).

Based on: SVS/AVF 2022 Clinical Practice Guidelines for Chronic Venous Disease.
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, num

LOGIC_KEY = "endovenousablation"


def _fmt_num(x: float) -> str:
    """Reproduce JS number-to-string in template literals (no trailing .0)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def assess(data: dict) -> dict:
    contraindications: list[str] = []
    rationale: list[str] = []
    optimization_steps: list[str] = []

    # Absolute contraindications
    if data.get("pregnancy"):
        contraindications.append("Pregnancy — defer elective ablation until postpartum")
    if data.get("activeInfection"):
        contraindications.append(
            "Active skin/soft tissue infection overlying target vein — treat infection first"
        )
    if data.get("nonAmbulatory"):
        contraindications.append(
            "Non-ambulatory patient — endovenous ablation not indicated; consider compression only"
        )
    if data.get("coagulopathy"):
        contraindications.append(
            "Uncorrected coagulopathy — manage anticoagulation per procedural guidelines"
        )

    if len(contraindications) > 0:
        return {
            "recommendation": "Endovenous Ablation Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Absolute contraindication(s) identified — address before proceeding."],
            "contraindications": contraindications,
            "optimizationSteps": [
                "Resolve contraindication(s) before reassessing candidacy",
                "Continue compression therapy in the interim",
            ],
            "modalityNote": "",
        }

    ceap_num = intnum(str(data.get("ceapClass") or "").replace("C", ""), 0)
    reflux_duration = num(data.get("refluxDuration"), 0)
    vein_diameter = num(data.get("veinDiameter"), 0)
    compression_weeks = num(data.get("compressionWeeks"), 0)
    vcss = num(data.get("vcssScore"), 0)

    gsv = data.get("gsv")
    ssv = data.get("ssv")
    duplex_confirmed = data.get("duplexConfirmed")
    standing_reflux = data.get("standingReflux")

    cor = "IIb"
    urgency = "Elective"

    # SVS 2022 Grade 1A: CEAP C2-C6 with confirmed GSV/SSV reflux after compression trial
    if (
        ceap_num >= 2
        and (gsv or ssv)
        and duplex_confirmed
        and standing_reflux
        and reflux_duration >= 0.5
        and compression_weeks >= 3
    ):
        cor = "I"
        urgency = "Urgent (Active/Healed Ulcer)" if ceap_num >= 5 else "Appropriate"
        rationale.append(
            f"CEAP {data.get('ceapClass')} with duplex-confirmed "
            f"{'GSV' if gsv else 'SSV'} reflux ≥{_fmt_num(reflux_duration)}s in standing position"
        )
        rationale.append("Compression therapy trial completed (≥3 weeks)")
        rationale.append(
            "SVS 2022 Grade 1A: Endovenous thermal ablation is recommended as first-line "
            "treatment for symptomatic truncal vein reflux"
        )
        if ceap_num >= 5:
            rationale.append(
                "Active or healed venous ulcer (C5-C6) — ablation reduces ulcer recurrence by 50–70%"
            )
    elif ceap_num >= 2 and (gsv or ssv) and duplex_confirmed and compression_weeks >= 3:
        cor = "IIa"
        urgency = "Reasonable"
        rationale.append(f"CEAP {data.get('ceapClass')} with duplex-confirmed truncal reflux")
        rationale.append("Compression trial completed — ablation is reasonable")
        if reflux_duration < 0.5:
            optimization_steps.append(
                "Reflux duration <0.5s — confirm with standing duplex; borderline reflux "
                "may not meet payer criteria"
            )
    elif ceap_num == 1 and (gsv or ssv) and duplex_confirmed:
        cor = "IIb"
        urgency = "Symptomatic C1 — Consider Conservative Management"
        rationale.append(
            "CEAP C1 (telangiectasias/reticular veins) — most payers require C2 or higher "
            "for thermal ablation"
        )
        optimization_steps.append(
            "Document CEAP C2 or higher varicosities on duplex before requesting auth"
        )
        optimization_steps.append("Consider sclerotherapy for isolated C1 disease")
    elif compression_weeks < 3:
        cor = "IIb"
        urgency = "Continue Compression Therapy"
        rationale.append(
            "Compression therapy trial insufficient — most payers require ≥3–6 weeks"
        )
        optimization_steps.append(
            "Continue graduated compression stockings (20–30 mmHg) for ≥6 weeks"
        )
        optimization_steps.append(
            "Document compliance and symptom response before requesting authorization"
        )
    elif not duplex_confirmed:
        cor = "IIb"
        urgency = "Duplex Ultrasound Required"
        rationale.append("Duplex ultrasound confirmation of reflux is required before ablation")
        optimization_steps.append(
            "Obtain bilateral lower extremity venous duplex with standing reflux protocol"
        )
    else:
        cor = "IIb"
        urgency = "Insufficient Criteria"
        optimization_steps.append("Ensure CEAP C2 or higher is documented")
        optimization_steps.append("Confirm duplex-documented reflux ≥0.5s in standing position")
        optimization_steps.append("Complete ≥6-week compression stocking trial")

    # Modality note
    if vein_diameter > 12:
        modality_note = (
            "Vein diameter >12 mm: RFA may have higher occlusion rates; consider MOCA or laser "
            "with higher energy settings. Some operators prefer phlebectomy for very large veins."
        )
    elif vein_diameter < 3:
        modality_note = (
            "Vein diameter <3 mm: Endovenous thermal ablation may be technically challenging; "
            "consider sclerotherapy as alternative."
        )
    else:
        modality_note = (
            "Vein diameter within standard range (3–12 mm): Both EVLA and RFA are appropriate "
            "with comparable 5-year occlusion rates (~95%)."
        )

    if data.get("priorDVT"):
        rationale.append(
            "Prior DVT: Confirm absence of post-thrombotic obstruction on duplex before ablation; "
            "obtain hematology consultation if thrombophilia suspected"
        )

    if vcss >= 8:
        rationale.append(
            f"VCSS {_fmt_num(vcss)} (moderate-severe) — supports medical necessity for ablation"
        )

    if cor == "I":
        recommendation = "Endovenous Ablation Recommended"
    elif cor == "IIa":
        recommendation = "Endovenous Ablation Reasonable"
    elif urgency == "Continue Compression Therapy":
        recommendation = "Continue Compression Therapy — Ablation Premature"
    elif urgency == "Duplex Ultrasound Required":
        recommendation = "Duplex Ultrasound Required Before Ablation"
    else:
        recommendation = "Insufficient Criteria for Ablation"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if ceap_num >= 4 else "B" if ceap_num >= 2 else "C",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
        "modalityNote": modality_note,
    }
