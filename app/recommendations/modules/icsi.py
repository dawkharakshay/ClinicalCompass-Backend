"""Intracytoplasmic Sperm Injection (ICSI) appropriateness.

Ported 1:1 from old_static_code/client/src/pages/ICSICompass.tsx (evaluate).
The decision logic lives inline in the Compass page; there is no separate
*Logic.ts file for ICSI.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "icsi"

_REFERENCES = [
    "Practice Committee of the ASRM. Intracytoplasmic sperm injection (ICSI) for non-male factor indications: a committee opinion. Fertil Steril. 2020;114(2):239-245.",
    "Van Steirteghem A, et al. High fertilization and implantation rates after intracytoplasmic sperm injection. Hum Reprod. 1993;8(7):1061-1066.",
    "Palermo G, et al. Pregnancies after intracytoplasmic injection of single spermatozoon into an oocyte. Lancet. 1992;340(8810):17-18.",
]


def assess(data: dict) -> dict:
    sperm_concentration = data.get("spermConcentration")
    # parseFloat(...) || 0 semantics in the TS input setters.
    morphology_percent = num(data.get("morphologyPercent"), 0)

    prior_failed = truthy(data.get("priorIVFFailedFertilization"))
    prior_low = truthy(data.get("priorIVFLowFertilization"))
    antisperm_antibodies = truthy(data.get("antispermAntibodies"))
    obstructive = truthy(data.get("obstructiveAzoospermia"))
    non_obstructive = truthy(data.get("nonObstructiveAzoospermia"))
    surgical_retrieval = truthy(data.get("surgicalSpermRetrieval"))
    frozen_sperm = truthy(data.get("frozenSperm"))
    unexplained = truthy(data.get("unexplainedIVFFailure"))

    warnings: list[str] = []
    rationale: list[str] = []

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "A"

    has_absolute_indication = (
        sperm_concentration == "severe"
        or sperm_concentration == "azoospermia"
        or obstructive
        or non_obstructive
        or surgical_retrieval
        or prior_failed
        or antisperm_antibodies
    )

    has_relative_indication = (
        sperm_concentration == "moderate"
        or prior_low
        or frozen_sperm
        or unexplained
        or morphology_percent < 4
    )

    if has_absolute_indication:
        recommendation = "indicated"
        procedure = "ICSI — absolute indication"
        cor = "I"
        loe = "A"
        if surgical_retrieval or obstructive or non_obstructive:
            rationale.append(
                "Surgical sperm retrieval: ICSI is required — conventional IVF "
                "insemination is not possible with surgically retrieved sperm."
            )
        if prior_failed:
            rationale.append(
                "Prior IVF with failed fertilization: ICSI is indicated to "
                "overcome fertilization failure."
            )
        if antisperm_antibodies:
            rationale.append(
                "Antisperm antibodies: ICSI bypasses the zona pellucida, "
                "overcoming antibody-mediated fertilization failure."
            )
        if sperm_concentration == "severe" or sperm_concentration == "azoospermia":
            rationale.append(
                "Severe male factor: total motile count is insufficient for "
                "conventional IVF insemination."
            )
    elif has_relative_indication:
        recommendation = "consider"
        procedure = "ICSI — relative indication (shared decision-making)"
        cor = "IIa"
        loe = "B"
        rationale.append(
            "Relative indication present: ICSI may improve fertilization rates "
            "but evidence for routine use in non-male factor is mixed (ASRM 2020)."
        )
        warnings.append(
            "ASRM 2020: ICSI for non-male factor indications is not routinely "
            "recommended without specific clinical justification."
        )
    else:
        recommendation = "not_indicated"
        procedure = "Conventional IVF insemination — ICSI not indicated"
        cor = "III"
        loe = "B"
        rationale.append(
            "No male factor or other ICSI indication identified. Conventional "
            "IVF insemination is appropriate."
        )
        warnings.append(
            "Routine ICSI for all IVF cycles is not supported by evidence and "
            "may not be covered by insurance without documented indication."
        )

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": list(_REFERENCES),
    }
