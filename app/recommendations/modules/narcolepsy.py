"""Narcolepsy Clinical Compass — diagnostic likelihood and AASM 2021 treatment.

Ported 1:1 from old_static_code/client/src/pages/NarcolepsyCompass.tsx (the
inline ``evaluate()`` function — there is no separate *Logic.ts engine).

ICSD-3 / AASM 2021 CPG criteria.
"""

from __future__ import annotations

import math

from app.recommendations.jslib import intnum, parse_float, truthy

LOGIC_KEY = "narcolepsy"


def _js_num(x: float) -> float | None:
    """Mirror a JS ``parseFloat`` result inside the returned dict.

    JS would carry NaN through; surface it as ``None`` for JSON-safe output
    (these fields are only populated meaningfully when the gating comparisons
    succeed, which never holds for NaN).
    """
    return None if math.isnan(x) else x


def assess(data: dict) -> dict:
    ess_num = parse_float(data.get("ess"))
    mslt_sol = parse_float(data.get("mslt_sol"))
    mslt_sorems = intnum(data.get("mslt_sorems"))
    psg_rem_latency = parse_float(data.get("psg_rem_latency"))

    excessive_daytime_sleepiness = ess_num >= 10
    mslt_positive = mslt_sol <= 8 and mslt_sorems >= 2
    csf_low = data.get("csf_hypocretin") == "low"
    psg_sorem_present = truthy(data.get("psg_performed")) and psg_rem_latency <= 15

    # ICSD-3 / AASM 2021 criteria
    diagnosis_likelihood = "low"
    diagnosis_type = data.get("type")

    cataplexy = truthy(data.get("cataplexy"))

    if cataplexy and (csf_low or mslt_positive):
        diagnosis_likelihood = "high"
        diagnosis_type = "type1"
    elif (not cataplexy) and mslt_positive and (not csf_low):
        diagnosis_likelihood = "high"
        diagnosis_type = "type2"
    elif excessive_daytime_sleepiness and (mslt_positive or psg_sorem_present):
        diagnosis_likelihood = "moderate"
    elif excessive_daytime_sleepiness:
        diagnosis_likelihood = "low"

    # Treatment recommendations per AASM 2021 CPG
    first_line: list[str] = []
    second_line: list[str] = []
    adjunctive: list[str] = []

    if diagnosis_likelihood != "low":
        # EDS treatment
        first_line.append("Modafinil 100–400 mg/day (AASM: Strong recommendation)")
        first_line.append("Pitolisant 17.8–35.6 mg/day (AASM: Strong recommendation)")
        first_line.append(
            "Sodium oxybate 4.5–9 g/night in 2 divided doses (AASM: Strong recommendation)"
        )
        first_line.append("Solriamfetol 75–150 mg/day (AASM: Strong recommendation)")

        if diagnosis_type == "type1" or cataplexy:
            first_line.append(
                "Sodium oxybate (also addresses cataplexy — AASM: Strong recommendation)"
            )
            first_line.append(
                "Pitolisant (also addresses cataplexy — AASM: Conditional recommendation)"
            )
            second_line.append("Venlafaxine 75–225 mg/day for cataplexy (AASM: Conditional)")
            second_line.append("Clomipramine 25–200 mg/day for cataplexy (AASM: Conditional)")

        adjunctive.append("Scheduled naps (15–20 min, 1–2x/day)")
        adjunctive.append("Sleep hygiene counseling")
        adjunctive.append("Driving restrictions counseling per state law")

    auth_required = diagnosis_likelihood != "low"
    appeal_strength = (
        "strong"
        if diagnosis_likelihood == "high"
        else "moderate"
        if diagnosis_likelihood == "moderate"
        else "weak"
    )

    key_findings: list[str] = []
    if excessive_daytime_sleepiness:
        key_findings.append(f"ESS score {_fmt_num(ess_num)} (≥10 indicates EDS)")
    if cataplexy:
        key_findings.append("Cataplexy present (pathognomonic for NT1)")
    if mslt_positive:
        key_findings.append("MSLT: SOL ≤8 min with ≥2 SOREMPs (AASM diagnostic threshold met)")
    if csf_low:
        key_findings.append("CSF hypocretin-1 ≤110 pg/mL (diagnostic for NT1)")
    if psg_sorem_present:
        key_findings.append("PSG: REM latency ≤15 min (sleep-onset REM period)")
    if truthy(data.get("comorbid_osa")):
        key_findings.append("Comorbid OSA — ensure adequate OSA treatment before MSLT")

    return {
        "diagnosisLikelihood": diagnosis_likelihood,
        "diagnosisType": diagnosis_type,
        "authRequired": auth_required,
        "appealStrength": appeal_strength,
        "firstLine": first_line,
        "secondLine": second_line,
        "adjunctive": adjunctive,
        "keyFindings": key_findings,
        "essNum": _js_num(ess_num),
        "msltPositive": mslt_positive,
        "csfLow": csf_low,
    }


def _fmt_num(x: float) -> str:
    """Render a JS number the way a template literal would (no trailing .0 for ints)."""
    if math.isnan(x):
        return "NaN"
    if x == int(x):
        return str(int(x))
    return repr(x)
