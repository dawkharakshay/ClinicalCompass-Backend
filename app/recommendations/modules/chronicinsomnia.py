"""Chronic Insomnia Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/ChronicInsomniaCompass.tsx
(the inline ``evaluate`` function; there is no separate *Logic.ts engine).
"""

from __future__ import annotations

import math

from app.recommendations.jslib import intnum, parse_float, truthy

LOGIC_KEY = "chronicinsomnia"


def assess(data: dict) -> dict:
    # const durationMonths = parseFloat(inputs.duration_months);
    duration_months = parse_float(data.get("duration_months"))
    # const isiScore = parseInt(inputs.isi_score);  (NaN -> 0 here; guarded by truthiness below)
    isi_score = intnum(data.get("isi_score"), 0)
    # const freqNights = parseFloat(inputs.frequency_nights_per_week);
    freq_nights = parse_float(data.get("frequency_nights_per_week"))

    daytime_impairment = data.get("daytime_impairment")
    cbti_response = data.get("cbti_response")
    type_ = data.get("type")

    # NaN >= 3 is false in JS; mirror that here.
    is_chronic_insomnia = bool(
        (not math.isnan(duration_months) and duration_months >= 3)
        and (not math.isnan(freq_nights) and freq_nights >= 3)
        and truthy(daytime_impairment)
    )

    # isiScore >= 22 ? "severe" : isiScore >= 15 ? "moderate" : "mild"
    if isi_score >= 22:
        severity = "severe"
    elif isi_score >= 15:
        severity = "moderate"
    else:
        severity = "mild"

    first_line: list[str] = []
    second_line: list[str] = []
    avoid_list: list[str] = []

    # AASM 2017 + April 2026 CPG
    first_line.append(
        "Cognitive Behavioral Therapy for Insomnia (CBT-I) — AASM: Strong recommendation (first-line for all chronic insomnia)"
    )

    if cbti_response == "partial" or cbti_response == "inadequate":
        # Pharmacologic options per AASM 2017 CPG
        if not truthy(data.get("age_over_65")) and not truthy(data.get("hepatic_impairment")):
            first_line.append(
                "Suvorexant (Belsomra) 10–20 mg — AASM: Strong recommendation (sleep onset + maintenance)"
            )
            first_line.append(
                "Lemborexant (Dayvigo) 5–10 mg — AASM: Strong recommendation (sleep onset + maintenance)"
            )
        if type_ == "sleep_maintenance" or type_ == "both" or type_ == "early_awakening":
            first_line.append(
                "Doxepin 3–6 mg — AASM: Strong recommendation (sleep maintenance only)"
            )
        if not truthy(data.get("comorbid_substance")):
            second_line.append("Eszopiclone (Lunesta) 1–3 mg — AASM: Conditional recommendation")
            second_line.append("Zolpidem (Ambien) 5–10 mg — AASM: Conditional recommendation")
            second_line.append(
                "Triazolam 0.125–0.25 mg — AASM: Conditional recommendation (short-term only)"
            )
        if truthy(data.get("comorbid_depression")):
            second_line.append(
                "Trazodone 50–150 mg — commonly used off-label; limited RCT evidence"
            )

    if cbti_response == "not_tried":
        first_line.append(
            "⚠️ CBT-I should be attempted before pharmacotherapy per AASM 2017 and 2026 guidelines"
        )

    # AASM April 2026: combination CBT-I + medication
    if cbti_response == "partial":
        first_line.append(
            "AASM April 2026 CPG: Combination CBT-I + pharmacotherapy conditionally recommended for partial CBT-I responders"
        )

    if truthy(data.get("age_over_65")):
        avoid_list.append("Benzodiazepines (fall risk, cognitive impairment — AASM: Against)")
        avoid_list.append("Z-drugs at standard doses (reduce dose by 50% — AASM: Conditional)")
        avoid_list.append("Diphenhydramine (Benadryl) — AASM: Against; anticholinergic risk")
    if truthy(data.get("comorbid_substance")):
        avoid_list.append("Benzodiazepines and Z-drugs (abuse potential)")
    if truthy(data.get("pregnancy")):
        avoid_list.append(
            "All pharmacologic agents — safety data insufficient; CBT-I is first-line"
        )

    avoid_list.append(
        "OTC antihistamines (diphenhydramine, doxylamine) — AASM: Against for chronic insomnia"
    )
    avoid_list.append(
        "Melatonin — AASM: Weak evidence for chronic insomnia; not recommended as primary treatment"
    )
    avoid_list.append("Tryptophan, valerian — AASM: Insufficient evidence")

    auth_required = cbti_response != "not_tried"
    appeal_strength = (
        "strong" if (is_chronic_insomnia and cbti_response != "not_tried") else "moderate"
    )

    key_findings: list[str] = []
    if is_chronic_insomnia:
        key_findings.append(
            f"Chronic insomnia disorder: ≥{_num_str(duration_months)} months, "
            f"≥{_num_str(freq_nights)} nights/week, with daytime impairment (ICSD-3 criteria met)"
        )
    if truthy(isi_score):
        key_findings.append(f"ISI score: {isi_score}/28 — {severity} insomnia")
    if cbti_response != "not_tried":
        resp = "Partial response" if cbti_response == "partial" else "Inadequate response"
        key_findings.append(f"CBT-I trial: {resp} — pharmacotherapy indicated")
    if truthy(data.get("comorbid_depression")):
        key_findings.append(
            "Comorbid depression — consider dual-action agent (trazodone, mirtazapine)"
        )
    if truthy(data.get("comorbid_osa")):
        key_findings.append(
            "Comorbid OSA — ensure PAP therapy optimized before treating residual insomnia"
        )

    return {
        "isChronicInsomnia": is_chronic_insomnia,
        "severity": severity,
        "firstLine": first_line,
        "secondLine": second_line,
        "avoidList": avoid_list,
        "authRequired": auth_required,
        "appealStrength": appeal_strength,
        "keyFindings": key_findings,
    }


def _num_str(x: float) -> str:
    """Render a float the way JS template-literal coercion would (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return repr(x)
