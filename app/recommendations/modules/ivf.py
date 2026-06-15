"""In Vitro Fertilization (IVF) Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/IVFCompass.tsx (the inline
``evaluate()`` function — there is no separate ivfLogic.ts). Matches the TS
branches, thresholds, COR/LOE assignments and string literals exactly.
"""

from __future__ import annotations

from app.recommendations.jslib import coalesce, num, to_bool

LOGIC_KEY = "ivf"

_REFERENCES = [
    "Practice Committee of the American Society for Reproductive Medicine. Definitions of infertility and recurrent pregnancy loss. Fertil Steril. 2020;113(3):533-535.",
    "Practice Committee of the ASRM. Guidance on the limits to the number of embryos to transfer. Fertil Steril. 2021;116(3):651-654.",
    "Zegers-Hochschild F, et al. International Committee for Monitoring Assisted Reproductive Technology (ICMART) and the World Health Organization (WHO) revised glossary of ART terminology. Fertil Steril. 2009;92(5):1520-1524.",
    "CDC ART Success Rates. National Summary Report. Centers for Disease Control and Prevention. 2022.",
    "ASRM Practice Committee. Optimizing natural fertility: a committee opinion. Fertil Steril. 2022;117(1):53-63.",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    female_age = num(data.get("femaleAge"), 0)
    infertility_duration = coalesce(data.get("infertilityDuration"), "gt12")
    ovarian_reserve = coalesce(data.get("ovarianReserve"), "normal")
    male_factor = coalesce(data.get("maleFactor"), "none")
    tubal_factor = to_bool(data.get("tubalFactor"))
    uterine_factor = to_bool(data.get("uterineFactor"))
    endometriosis = to_bool(data.get("endometriosis"))
    unexplained = to_bool(data.get("unexplained"))
    prior_iui_attempts = num(data.get("priorIUIAttempts"), 0)
    prior_ivf_attempts = num(data.get("priorIVFAttempts"), 0)
    prior_ivf_success = to_bool(data.get("priorIVFSuccess"))
    state_mandate = to_bool(data.get("stateMandate"))
    oncology_indication = to_bool(data.get("oncologyIndication"))

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "A"
    success_rate = ""

    # Age-based success rates (CDC 2022 data)
    if female_age < 35:
        success_rate = "~40–50% live birth per cycle"
    elif female_age < 38:
        success_rate = "~30–40% live birth per cycle"
    elif female_age < 41:
        success_rate = "~20–30% live birth per cycle"
    elif female_age < 43:
        success_rate = "~10–15% live birth per cycle"
    else:
        success_rate = "~3–5% live birth per cycle (donor egg discussion recommended)"

    # Determine IVF indication
    has_indication = (
        tubal_factor
        or uterine_factor
        or male_factor == "severe"
        or male_factor == "azoospermia"
        or ovarian_reserve == "diminished"
        or ovarian_reserve == "poor"
        or ovarian_reserve == "premature_failure"
        or oncology_indication
        or (prior_iui_attempts >= 3 and infertility_duration == "gt12")
        or (unexplained and prior_iui_attempts >= 3)
        or endometriosis
    )

    if oncology_indication:
        recommendation = "indicated"
        procedure = "IVF with embryo cryopreservation (oncofertility)"
        cor = "I"
        loe = "A"
        rationale.append(
            "Oncofertility: IVF with embryo cryopreservation is the most established method of fertility preservation before gonadotoxic therapy (ASRM/ASCO)."
        )
        warnings.append(
            "Time-sensitive: coordinate with oncology team to begin IVF stimulation before chemotherapy/radiation."
        )
    elif tubal_factor:
        recommendation = "indicated"
        procedure = "IVF (tubal factor infertility — first-line)"
        cor = "I"
        loe = "A"
        rationale.append(
            "Bilateral tubal occlusion or severe tubal damage: IVF is first-line treatment per ASRM guidelines."
        )
    elif male_factor == "severe" or male_factor == "azoospermia":
        recommendation = "indicated"
        procedure = "IVF with ICSI (severe male factor)"
        cor = "I"
        loe = "A"
        rationale.append(
            "Severe male factor or azoospermia: IVF/ICSI is required — natural conception or IUI is not feasible."
        )
    elif has_indication:
        recommendation = "indicated"
        procedure = "IVF"
        cor = "I"
        loe = "A"
        rationale.append("Multiple infertility factors identified meeting ASRM criteria for IVF.")
    elif infertility_duration == "gt12" and prior_iui_attempts < 3:
        recommendation = "consider"
        procedure = "IUI trials before IVF (3 cycles recommended)"
        cor = "IIa"
        loe = "B"
        rationale.append(
            "ASRM recommends 3–6 IUI cycles before proceeding to IVF in unexplained or mild infertility without absolute IVF indications."
        )
    else:
        recommendation = "not_indicated"
        procedure = "Continue evaluation / IUI trials"
        rationale.append(
            "IVF criteria not yet met: complete infertility workup and consider IUI trials first."
        )

    if female_age >= 38:
        warnings.append(
            f"Age {_fmt_age(female_age)}: ASRM recommends expedited evaluation and treatment. Do not delay IVF unnecessarily."
        )
    if female_age >= 40 and ovarian_reserve == "poor":
        warnings.append(
            "Advanced age + poor ovarian reserve: discuss donor oocyte IVF as an alternative with significantly higher success rates."
        )
    if prior_ivf_attempts >= 3 and not prior_ivf_success:
        warnings.append(
            "3+ failed IVF cycles: consider PGT-A, immunologic evaluation, or donor oocyte discussion."
        )
    if state_mandate:
        rationale.append(
            "State infertility mandate applies: insurer is legally required to cover IVF per state law."
        )

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "successRate": success_rate,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": references,
    }


def _fmt_age(age: float) -> str:
    """Render age in the warning string as JS would interpolate the number
    (integers without a trailing ``.0``)."""
    return str(int(age)) if float(age).is_integer() else str(age)
