"""Preimplantation Genetic Testing (PGT) Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/PGTCompass.tsx (the inline
``evaluate(inputs)`` function — there is no separate *Logic.ts for this module).
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "pgt"

_REFERENCES = [
    "Practice Committee of the ASRM. The use of preimplantation genetic testing for aneuploidy (PGT-A): a committee opinion. Fertil Steril. 2018;109(3):429-436.",
    "ACOG Committee Opinion No. 682. Microarrays and Next-Generation Sequencing Technology. Obstet Gynecol. 2016;128(6):e262-e268.",
    "Munne S, et al. Preimplantation genetic testing for aneuploidy versus morphology as selection criteria for single frozen-thawed embryo transfer in good-prognosis patients. Fertil Steril. 2019;112(6):1071-1079.",
    "ASRM Practice Committee. Preimplantation genetic testing: a committee opinion. Fertil Steril. 2018;109(3):429-436.",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    pgt_type = data.get("pgtType")
    female_age = num(data.get("femaleAge"), 0)
    recurrent_pregnancy_loss = to_bool(data.get("recurrentPregnancyLoss"))
    rpl_count = num(data.get("rplCount"), 0)
    prior_aneuploid_pregnancy = to_bool(data.get("priorAneuploidPregnancy"))
    known_genetic_disorder = to_bool(data.get("knownGeneticDisorder"))
    gene_disorder_name = data.get("geneDisorderName") or ""
    chromosomal_translocation = to_bool(data.get("chromosomalTranslocation"))
    repeated_ivf_failure = to_bool(data.get("repeatedIVFFailure"))
    ivf_failure_count = num(data.get("ivfFailureCount"), 0)
    sex_selection = to_bool(data.get("sexSelection"))

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "B"

    if pgt_type == "pgt_m" and known_genetic_disorder:
        recommendation = "indicated"
        procedure = "PGT-M (monogenic/single gene disorder)"
        cor, loe = "I", "A"
        rationale.append(
            f"Known genetic disorder ({gene_disorder_name or 'specified'}): "
            "PGT-M is indicated to prevent transmission of serious genetic disease."
        )
        rationale.append(
            "ASRM: PGT-M is appropriate for couples at risk of transmitting serious monogenic disorders."
        )
    elif pgt_type == "pgt_sr" and chromosomal_translocation:
        recommendation = "indicated"
        procedure = "PGT-SR (structural rearrangement — translocation)"
        cor, loe = "I", "A"
        rationale.append(
            "Chromosomal translocation: PGT-SR is indicated to select embryos with balanced chromosomal complement."
        )
    elif pgt_type == "pgt_a":
        # JS: && binds tighter than ||
        has_strong_indication = (
            (recurrent_pregnancy_loss and rpl_count >= 2)
            or prior_aneuploid_pregnancy
            or female_age >= 38
            or (repeated_ivf_failure and ivf_failure_count >= 2)
        )
        if has_strong_indication:
            recommendation = "indicated"
            procedure = "PGT-A (aneuploidy screening)"
            cor, loe = "IIa", "B"
            if recurrent_pregnancy_loss:
                rationale.append(
                    f"Recurrent pregnancy loss ({_numfmt(rpl_count)} losses): "
                    "PGT-A may identify aneuploid embryos contributing to pregnancy loss."
                )
            if female_age >= 38:
                rationale.append(
                    f"Advanced maternal age ({_numfmt(female_age)}): higher aneuploidy rate — "
                    "PGT-A may improve single embryo transfer outcomes."
                )
            if repeated_ivf_failure:
                rationale.append(
                    f"Repeated IVF failure ({_numfmt(ivf_failure_count)} cycles): "
                    "PGT-A may identify viable euploid embryos."
                )
            warnings.append(
                "PGT-A: ASRM notes evidence for clinical benefit is strongest in RPL and "
                "repeated IVF failure. Routine use in all IVF cycles is not universally recommended."
            )
        else:
            recommendation = "consider"
            procedure = "PGT-A — consider with shared decision-making"
            cor, loe = "IIb", "C"
            rationale.append(
                "No strong indication for PGT-A identified. Discuss risks/benefits with patient "
                "including embryo biopsy risk and potential for inconclusive results."
            )
    else:
        recommendation = "not_indicated"
        procedure = "PGT not indicated based on current inputs"

    if sex_selection:
        warnings.append(
            "Non-medical sex selection: ASRM considers non-medical sex selection ethically "
            "controversial. Most insurers will not cover PGT for this indication."
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


def _numfmt(x: float) -> str:
    """Render a number like JS string interpolation: integers without a trailing
    ``.0`` (e.g. ``38`` not ``38.0``)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)
