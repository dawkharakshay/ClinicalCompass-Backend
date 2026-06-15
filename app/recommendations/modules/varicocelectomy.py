"""Varicocelectomy (surgical varicocele repair) appropriateness.

Ported 1:1 from the inline ``evaluate()`` engine in
old_static_code/client/src/pages/VaricocelectomyCompass.tsx
("Varicocelectomy Clinical Compass").

NOTE: This is the surgical-repair engine embedded in the Compass page. The
separate varicoceleLogic.ts (assessVaricocele) is the embolization-focused
engine for the distinct "varicocele" module and is ported elsewhere.
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "varicocelectomy"

_REFERENCES = [
    "Schlegel PN, et al. Diagnosis and treatment of infertility in men: AUA/ASRM guideline. J Urol. 2021;205(2):397-398.",
    "Baazeem A, et al. Varicocele and male factor infertility treatment: a new meta-analysis and review of the role of varicocele repair. Eur Urol. 2011;59(5):796-808.",
    "Nork JJ, et al. The AUA/ASRM varicocele guideline: implications for the practicing urologist. Urol Pract. 2022;9(1):1-8.",
    "Kirby EW, et al. Microsurgical varicocelectomy vs. embolization: a meta-analysis. J Urol. 2016;196(5):1371-1379.",
    "EAU Guidelines on Male Infertility. European Association of Urology. 2024.",
]


def assess(data: dict) -> dict:
    grade = data.get("grade")
    sperm_concentration = num(data.get("spermConcentration"), 0)
    progressive_motility = num(data.get("progressiveMotility"), 0)
    morphology_kruger = num(data.get("morphologyKruger"), 0)
    total_motile_count = num(data.get("totalMotileCount"), 0)
    testis_volume_diff = num(data.get("testisVolumeDiff"), 0)
    infertility_duration = num(data.get("infertilityDuration"), 0)
    partner_age = num(data.get("partnerAge"), 0)
    fsh_level = num(data.get("fshLevel"), 0)
    adolescent = to_bool(data.get("adolescent"))
    pain_present = to_bool(data.get("painPresent"))
    prior_varicocelectomy = to_bool(data.get("priorVaricocelectomy"))

    warnings: list[str] = []
    rationale: list[str] = []

    recommendation = "not_indicated"
    procedure = "Observation"
    cor = "III"
    loe = "B"

    # AUA/ASRM 2021 indications
    abnormal_semen = (
        sperm_concentration < 15
        or progressive_motility < 32
        or morphology_kruger < 4
        or total_motile_count < 9
    )
    palpable_varicocele = grade in ("I", "II", "III")
    clinically_significant = palpable_varicocele and grade != "subclinical"

    if adolescent:
        if testis_volume_diff >= 20:
            recommendation = "indicated"
            procedure = "Microsurgical Varicocelectomy"
            cor = "IIa"
            loe = "B"
            rationale.append(
                "Adolescent with ≥20% testicular volume differential: AUA/ASRM recommend repair to prevent progressive testicular injury."
            )
        else:
            recommendation = "consider"
            procedure = "Observation with annual semen analysis"
            rationale.append(
                "Adolescent with <20% volume differential: observation with annual follow-up is appropriate."
            )
    elif pain_present and clinically_significant:
        recommendation = "consider"
        procedure = "Microsurgical Varicocelectomy (pain indication)"
        cor = "IIb"
        loe = "C"
        rationale.append(
            "Varicocele-associated scrotal pain: surgical repair is reasonable when pain is refractory to conservative management."
        )
    elif clinically_significant and abnormal_semen and infertility_duration >= 12:
        recommendation = "indicated"
        procedure = "Microsurgical Varicocelectomy (subinguinal approach preferred)"
        cor = "I"
        loe = "A"
        rationale.append(
            "Palpable varicocele + abnormal semen parameters + ≥12 months infertility: AUA/ASRM Grade A recommendation for repair."
        )
        rationale.append(
            "Meta-analysis (Baazeem 2011): varicocelectomy improves sperm concentration, motility, and morphology with OR 2.87 for spontaneous pregnancy."
        )
    elif grade == "subclinical":
        recommendation = "not_indicated"
        procedure = "No repair — subclinical varicocele"
        cor = "III"
        loe = "A"
        rationale.append(
            "Subclinical varicocele: AUA/ASRM explicitly recommend against repair — no evidence of benefit."
        )
        warnings.append(
            "Subclinical varicoceles detected only on ultrasound should NOT be repaired per AUA/ASRM guidelines."
        )
    else:
        recommendation = "not_indicated"
        procedure = "Observation"
        rationale.append(
            "Criteria for repair not met: requires palpable varicocele + abnormal semen + ≥12 months infertility (or pain/adolescent indications)."
        )

    if partner_age > 37:
        warnings.append(
            f"Partner age {_fmt(partner_age)}: consider IVF/ICSI as concurrent or alternative strategy given diminished ovarian reserve."
        )
    if fsh_level > 10:
        warnings.append(
            f"Elevated FSH ({_fmt(fsh_level)}): suggests primary spermatogenic impairment; varicocelectomy benefit may be limited."
        )
    if prior_varicocelectomy:
        warnings.append(
            "Prior varicocelectomy: recurrence repair is appropriate if palpable varicocele recurs with abnormal semen."
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


def _fmt(x: float) -> str:
    """Render a number the way JS template interpolation would (integers
    without a trailing ``.0``)."""
    if x == int(x):
        return str(int(x))
    return str(x)
