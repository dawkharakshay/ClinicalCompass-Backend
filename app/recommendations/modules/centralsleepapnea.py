"""Central Sleep Apnea Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/CentralSleepApneaCompass.tsx
(the inline ``evaluate(inputs)`` function). There is no separate *Logic.ts file
for this module; the decision logic lives inline in the Compass page.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "centralsleepapnea"


def assess(data: dict) -> dict:
    ahi = parse_float(data.get("ahi"))
    cai = parse_float(data.get("cai"))
    cai_percent = parse_float(data.get("cai_percent"))
    bmi = parse_float(data.get("bmi"))
    ef = parse_float(data.get("ef_percent"))

    csa_diagnosis = cai >= 5 and cai_percent > 50
    severity = "severe" if ahi >= 30 else ("moderate" if ahi >= 15 else "mild")

    recommendations: list[str] = []
    contraindications: list[str] = []
    notes: list[str] = []

    etiology = data.get("etiology")

    # AASM 2025 CSA CPG
    if etiology == "cheyneStokes" or data.get("comorbid_hf"):
        if data.get("lvef_reduced") or ef < 45:
            contraindications.append(
                "ASV is CONTRAINDICATED in HFrEF (EF <45%) with predominantly CSA — AASM 2025 / SERVE-HF trial: increased cardiovascular mortality"
            )
            recommendations.append(
                "Optimize heart failure therapy (ACE-I/ARB, beta-blocker, diuretics, SGLT2 inhibitor)"
            )
            recommendations.append(
                "CPAP: Conditionally recommended for Cheyne-Stokes respiration in HFrEF (AASM 2025)"
            )
            recommendations.append(
                "Supplemental oxygen: Conditionally recommended for CSA-CSR in HFrEF"
            )
        else:
            recommendations.append(
                "ASV: Conditionally recommended for CSA-CSR in HFpEF (EF ≥45%) — AASM 2025"
            )
            recommendations.append(
                "CPAP: Conditionally recommended as first-line for CSA-CSR"
            )
    elif etiology == "opioid" or data.get("opioid_use"):
        recommendations.append(
            "Reduce opioid dose if clinically feasible (most effective intervention)"
        )
        recommendations.append(
            "BPAP with backup rate: Conditionally recommended for opioid-induced CSA — AASM 2025"
        )
        recommendations.append(
            "ASV: Conditionally recommended for opioid-induced CSA — AASM 2025"
        )
        opioid_mme = data.get("opioid_mme")
        mme = opioid_mme if truthy(opioid_mme) else "?"
        notes.append(
            f"Opioid dose: {mme} MME/day — CSA risk increases significantly above 200 MME/day"
        )
    elif etiology == "treatmentEmergent":
        recommendations.append(
            "Continue CPAP — treatment-emergent CSA often resolves within 1–3 months"
        )
        recommendations.append(
            "If persistent ≥3 months: switch to ASV (Conditionally recommended — AASM 2025)"
        )
        recommendations.append("If ASV not tolerated: BPAP with backup rate")
    elif etiology == "idiopathic":
        recommendations.append(
            "CPAP: Suggested as initial therapy for idiopathic CSA — AASM 2025"
        )
        recommendations.append("ASV: Conditionally recommended if CPAP inadequate")
        recommendations.append(
            "Acetazolamide 250–500 mg BID: Conditionally recommended for idiopathic CSA"
        )
    else:
        recommendations.append(
            "CPAP: First-line trial for most CSA etiologies — AASM 2025"
        )
        recommendations.append(
            "ASV: Conditionally recommended if CPAP inadequate (except HFrEF)"
        )

    # GLP-1 / Zepbound note for comorbid obesity
    if data.get("comorbid_obesity") or bmi >= 30:
        notes.append(
            "GLP-1/GIP Agonist (Tirzepatide/Zepbound): FDA-approved December 2024 for moderate-to-severe OSA with obesity. SURMOUNT-OSA trial: 50.7% mean AHI reduction (vs 29.3% placebo). Primarily studied for OSA, but weight loss may improve CSA in obese patients with CSA-OSA overlap. Prior auth required; BMI ≥30 with OSA diagnosis required."
        )

    auth_required = True
    appeal_strength = "strong" if csa_diagnosis else "moderate"

    key_findings: list[str] = []
    if truthy(ahi):
        key_findings.append(f"AHI: {_n(ahi)} events/hour — {severity} sleep apnea")
    if truthy(cai):
        cai_suffix = f" ({_n(cai_percent)}% of total events)" if truthy(cai_percent) else ""
        key_findings.append(
            f"Central Apnea Index (CAI): {_n(cai)} events/hour{cai_suffix}"
        )
    if csa_diagnosis:
        key_findings.append("CSA diagnosis criteria met: CAI ≥5 with >50% central events")
    if data.get("lvef_reduced"):
        key_findings.append("⚠️ Reduced EF — ASV CONTRAINDICATED (SERVE-HF / AASM 2025)")
    if data.get("opioid_use"):
        opioid_mme = data.get("opioid_mme")
        mme = opioid_mme if truthy(opioid_mme) else "dose not specified"
        key_findings.append(
            f"Opioid use: {mme} MME/day — opioid-induced CSA etiology"
        )

    return {
        "csaDiagnosis": csa_diagnosis,
        "severity": severity,
        "recommendations": recommendations,
        "contraindications": contraindications,
        "notes": notes,
        "authRequired": auth_required,
        "appealStrength": appeal_strength,
        "keyFindings": key_findings,
    }


def _n(x: float) -> str:
    """Render a parsed float like JS template-literal coercion (no trailing .0
    for integral values)."""
    if x == int(x):
        return str(int(x))
    return str(x)
