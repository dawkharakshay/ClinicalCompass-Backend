"""RLS / PLMD Clinical Compass.

Ported 1:1 from the inline ``evaluate(inputs)`` function in
old_static_code/client/src/pages/RLSPLMDCompass.tsx.

There is no separate ``*Logic.ts`` engine for this module; the decision logic
lives inline in the Compass page. Implements the AASM 2024 RLS/PLMD CPG flow.
"""

from __future__ import annotations

from app.recommendations.jslib import intnum, parse_float, truthy

LOGIC_KEY = "rlsplmd"


def assess(data: dict) -> dict:
    # parseInt(inputs.irlss_score) — empty/NaN behaves like 0 for all the
    # comparisons and the `if (irlss)` truthiness check below.
    irlss = intnum(data.get("irlss_score"), 0)
    ferritin = parse_float(data.get("ferritin"))
    egfr = parse_float(data.get("egfr"))

    if irlss >= 31:
        severity = "severe"
    elif irlss >= 21:
        severity = "moderate-severe"
    elif irlss >= 11:
        severity = "moderate"
    elif irlss >= 1:
        severity = "mild"
    else:
        severity = data.get("severity")

    transferrin_sat = parse_float(data.get("transferrin_sat"))
    # NaN comparisons are False in Python (matching JS) so unparseable
    # ferritin/transferrin values yield ironDeficient = False.
    iron_deficient = (ferritin < 75) or (ferritin < 100 and transferrin_sat < 20)

    recommendations: list[str] = []
    contraindications: list[str] = []
    notes: list[str] = []

    # AASM 2024 RLS/PLMD CPG — Iron first
    if iron_deficient:
        if not truthy(data.get("iron_infusion_tried")):
            recommendations.append(
                "IV Ferric Carboxymaltose (Injectafer): STRONGLY RECOMMENDED for RLS with serum ferritin <75 ng/mL or ferritin <100 with transferrin sat <20% — AASM 2024 CPG"
            )
            recommendations.append(
                "Target serum ferritin ≥75 ng/mL (ideally ≥100 ng/mL) before initiating pharmacotherapy"
            )
        else:
            notes.append(
                "IV iron infusion previously attempted — reassess ferritin response before escalating pharmacotherapy"
            )

    # Alpha-2-delta ligands — STRONGLY RECOMMENDED
    if not truthy(data.get("prior_gabapentin_enacarbil")):
        recommendations.append(
            "Gabapentin Enacarbil (Horizant): STRONGLY RECOMMENDED — AASM 2024 CPG. Preferred alpha-2-delta ligand for RLS; extended-release formulation with consistent bioavailability"
        )
    if not truthy(data.get("prior_pregabalin")):
        recommendations.append(
            "Pregabalin (Lyrica): STRONGLY RECOMMENDED — AASM 2024 CPG. Effective for RLS and comorbid anxiety/pain"
        )
    if not truthy(data.get("prior_gabapentin")):
        recommendations.append(
            "Gabapentin (Neurontin): STRONGLY RECOMMENDED — AASM 2024 CPG. Dose 300–1800 mg QHS; adjust for renal function"
        )

    # Dopamine agonists — CONDITIONALLY AGAINST
    if truthy(data.get("prior_pramipexole")) or truthy(data.get("prior_ropinirole")):
        if truthy(data.get("augmentation")):
            contraindications.append(
                "⚠️ AUGMENTATION DOCUMENTED: Dopamine agonists (pramipexole, ropinirole) are CONDITIONALLY RECOMMENDED AGAINST as first-line therapy per AASM 2024 CPG due to augmentation risk. Taper and transition to alpha-2-delta ligand."
            )
        else:
            notes.append(
                "Dopamine agonists (pramipexole, ropinirole) are now CONDITIONALLY RECOMMENDED AGAINST as first-line therapy per AASM 2024 CPG due to augmentation risk (symptoms worsen over time, spread to arms, occur earlier in day). Monitor for augmentation using IRLSS trends."
            )
    else:
        notes.append(
            "AASM 2024 CPG Update: Dopamine agonists (pramipexole, ropinirole) are now CONDITIONALLY RECOMMENDED AGAINST as first-line therapy due to augmentation risk. Prefer alpha-2-delta ligands as first-line pharmacotherapy."
        )

    # Renal adjustment
    if truthy(data.get("renal_impairment")) or egfr < 60:
        egfr_disp = data.get("egfr") if truthy(data.get("egfr")) else "reduced"
        notes.append(
            f"Renal impairment (eGFR: {egfr_disp}): Dose-adjust gabapentin and pregabalin. Gabapentin enacarbil is contraindicated in CrCl <30 mL/min. Consider low-dose oxycodone CR or methadone for severe refractory RLS in renal failure."
        )

    # Pregnancy
    if truthy(data.get("pregnancy")):
        recommendations.append(
            "Pregnancy: Avoid pharmacotherapy in first trimester. IV iron supplementation preferred. Low-dose clonazepam or opioids (with obstetric guidance) for severe refractory RLS in second/third trimester."
        )
        notes.append(
            "All RLS medications carry pregnancy risks — consult MFM/obstetrics before initiating."
        )

    # PLMD
    plmi = parse_float(data.get("plmi"))
    if truthy(data.get("plm_diagnosis")) and plmi >= 15:
        recommendations.append(
            f"PLMD (PLMI: {data.get('plmi')} events/hour): Alpha-2-delta ligands (gabapentin, pregabalin) are preferred. Clonazepam 0.5–2 mg QHS: CONDITIONALLY RECOMMENDED for PLMD — AASM 2024 CPG."
        )

    key_findings: list[str] = []
    if truthy(irlss):
        key_findings.append(f"IRLSS Score: {irlss}/40 — {severity} RLS")
    if truthy(data.get("plmi")):
        suffix = " — PLMD diagnosis criteria met" if plmi >= 15 else ""
        key_findings.append(f"PLMI: {data.get('plmi')} events/hour{suffix}")
    if iron_deficient:
        ferritin_disp = data.get("ferritin") if truthy(data.get("ferritin")) else "?"
        key_findings.append(
            f"Iron deficiency: Ferritin {ferritin_disp} ng/mL — IV iron strongly recommended"
        )
    if truthy(data.get("augmentation")):
        key_findings.append("⚠️ Augmentation documented — dopamine agonist taper indicated")

    auth_required = True
    appeal_strength = "strong" if (truthy(data.get("rls_diagnosis")) and irlss >= 11) else "moderate"

    return {
        "severity": severity,
        "recommendations": recommendations,
        "contraindications": contraindications,
        "notes": notes,
        "keyFindings": key_findings,
        "authRequired": auth_required,
        "appealStrength": appeal_strength,
        "ironDeficient": iron_deficient,
    }
