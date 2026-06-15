"""Ovulation Induction Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/OvulationInductionCompass.tsx
(the ``evaluate`` function — logic is inline in the Compass page, there is no
separate *Logic.ts file).
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "ovulationinduction"

_REFERENCES = [
    "Legro RS, et al. Diagnosis and Treatment of Polycystic Ovary Syndrome: An Endocrine Society Clinical Practice Guideline. J Clin Endocrinol Metab. 2013;98(12):4565-4592.",
    "Thessaloniki ESHRE/ASRM-Sponsored PCOS Consensus Workshop Group. Consensus on infertility treatment related to polycystic ovary syndrome. Fertil Steril. 2008;89(3):505-522.",
    "Legro RS, et al. Letrozole versus clomiphene for infertility in the polycystic ovary syndrome. N Engl J Med. 2014;371(2):119-129.",
    "Practice Committee of the ASRM. Use of clomiphene citrate in infertile women. Fertil Steril. 2013;100(2):341-348.",
]


def _fmt_bmi(value: object) -> str:
    """Reproduce JS string interpolation of a numeric BMI (e.g. ``30`` not
    ``30.0``, ``30.5`` preserved)."""
    f = parse_float(value)
    if f != f:  # NaN
        return str(value)
    return str(int(f)) if f == int(f) else str(f)


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    anovulation_cause = data.get("anovulationCause")
    bmi_raw = data.get("bmi")
    bmi = parse_float(bmi_raw)
    prior_letrozole = parse_float(data.get("priorLetrozoleTrials"))
    prior_clomiphene = parse_float(data.get("priorClomipheneTrials"))
    prior_gonadotropin = parse_float(data.get("priorGonadotropinTrials"))
    hyperprolactinemia_treated = truthy(data.get("hyperprolactinemiaTreated"))
    thyroid_treated = truthy(data.get("thyroidTreated"))

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "A"

    if anovulation_cause == "hyperprolactinemia" and not hyperprolactinemia_treated:
        recommendation = "not_indicated"
        procedure = "Treat hyperprolactinemia first (dopamine agonist)"
        cor, loe = "I", "A"
        rationale.append(
            "Hyperprolactinemia: treat with cabergoline or bromocriptine first. Ovulation induction before treating hyperprolactinemia is not indicated."
        )
    elif anovulation_cause == "thyroid" and not thyroid_treated:
        recommendation = "not_indicated"
        procedure = "Treat thyroid disorder first"
        cor, loe = "I", "A"
        rationale.append(
            "Thyroid disorder: normalize thyroid function before ovulation induction. Hypothyroidism and hyperthyroidism both impair ovulation."
        )
    elif anovulation_cause == "poi":
        recommendation = "not_indicated"
        procedure = "Ovulation induction not effective for POI — consider donor oocyte"
        cor, loe = "III", "A"
        warnings.append(
            "Premature ovarian insufficiency (POI): ovulation induction is not effective. Spontaneous ovulation occurs in only 5–10% of cases. Donor oocyte IVF is the most effective treatment."
        )
    elif anovulation_cause == "pcos":
        if prior_letrozole == 0 and prior_clomiphene == 0:
            recommendation = "indicated"
            procedure = "Letrozole (first-line for PCOS) — 2.5–7.5 mg days 3–7"
            cor, loe = "I", "A"
            rationale.append(
                "PCOS: letrozole is first-line ovulation induction per ASRM/Endocrine Society (Legro et al., NEJM 2014 — higher live birth rate than clomiphene)."
            )
        elif prior_letrozole < 6:
            recommendation = "indicated"
            procedure = f"Continue letrozole trials ({_fmt_bmi(data.get('priorLetrozoleTrials'))} completed, up to 6 recommended)"
            cor, loe = "I", "A"
            rationale.append(
                "Continue letrozole — up to 6 cycles are appropriate before escalating to gonadotropins or IVF."
            )
        elif prior_gonadotropin == 0:
            recommendation = "indicated"
            procedure = "Gonadotropin ovulation induction (FSH/LH) — step-up protocol"
            cor, loe = "I", "A"
            rationale.append(
                "Failed 6+ letrozole cycles: gonadotropin ovulation induction is the next step per ASRM guidelines."
            )
            warnings.append(
                "Gonadotropins carry higher risk of multiple gestation and OHSS. Careful monitoring with serial ultrasound required."
            )
        else:
            recommendation = "consider"
            procedure = "Consider IVF — multiple OI failures"
            cor, loe = "IIa", "B"
            rationale.append(
                "Multiple failed ovulation induction cycles: IVF may be more cost-effective and efficient at this point."
            )
        if bmi >= 30:
            warnings.append(
                f"BMI {_fmt_bmi(bmi_raw)}: weight loss of 5–10% may restore ovulation in PCOS. Lifestyle modification should be concurrent with OI."
            )
    else:
        recommendation = "indicated"
        procedure = "Ovulation induction — individualized protocol"
        cor, loe = "IIa", "B"
        rationale.append(
            "Anovulation identified: ovulation induction is indicated after treating reversible causes."
        )

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": references,
    }
