"""Vasectomy Reversal Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/VasectomyReversalCompass.tsx
(the inline ``evaluate()`` function — this module has no separate *Logic.ts file).
"""

from __future__ import annotations

from app.recommendations.jslib import num, to_bool

LOGIC_KEY = "vasectomyreversal"

_REFERENCES = [
    "Belker AM, et al. Results of 1,469 microsurgical vasectomy reversals by the Vasovasostomy Study Group. J Urol. 1991;145(3):505-511.",
    "Kolettis PN, Thomas AJ Jr. Vasoepididymostomy for vasectomy reversal: a critical assessment in the era of intracytoplasmic sperm injection. J Urol. 1997;158(2):467-470.",
    "Practice Committee of the American Society for Reproductive Medicine. Vasectomy reversal. Fertil Steril. 2015;104(3):e1-e8.",
    "Wosnitzer MS, Goldstein M. Obstructive azoospermia. Urol Clin North Am. 2014;41(1):83-95.",
    "Jarvi K, et al. CUA Guideline: The workup of azoospermic males. Can Urol Assoc J. 2010;4(3):163-167.",
]


def _sperm_in_vas(value):
    """Replicate the TS tri-state ``spermInVas: boolean | null``.

    In the source UI the select maps to: null (Unknown/Pre-operative),
    True (Yes), or False (No). The only branch that reads it uses a strict
    ``=== false`` comparison, so we must distinguish an explicit False from a
    missing/None value. Returns True, False, or None.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"unknown", "", "pre-operative", "preoperative"}:
            return None
        if s in {"yes", "true", "1", "y", "on"}:
            return True
        if s in {"no", "false", "0", "n", "off"}:
            return False
        return None
    return to_bool(value)


def assess(data: dict) -> dict:
    years_since_vasectomy = num(data.get("yearsSinceVasectomy"), 0)
    prior_vasectomy_reversal = to_bool(data.get("priorVasectomyReversal"))
    sperm_in_vas = _sperm_in_vas(data.get("spermInVas"))
    partner_age = num(data.get("partnerAge"), 0)
    antisperm_antibodies = to_bool(data.get("antispermAntibodies"))
    epididymal_obstruction = to_bool(data.get("epididymalObstruction"))
    testis_volume = data.get("testisVolume") if data.get("testisVolume") is not None else "normal"
    fsh_level = num(data.get("fshLevel"), 0)

    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    # Obstructive interval prognosis
    if years_since_vasectomy <= 3:
        patency_rate, pregnancy_rate = "97%", "76%"
    elif years_since_vasectomy <= 8:
        patency_rate, pregnancy_rate = "88%", "53%"
    elif years_since_vasectomy <= 14:
        patency_rate, pregnancy_rate = "79%", "44%"
    else:
        patency_rate, pregnancy_rate = "71%", "30%"

    rationale.append(
        f"Obstructive interval of {_num_str(years_since_vasectomy)} years: expected patency rate "
        f"~{patency_rate}, pregnancy rate ~{pregnancy_rate} (Vasovasostomy Study Group, Belker 1991)."
    )

    # Procedure type
    procedure = "Vasovasostomy (VV)"
    procedure_rationale = "Intraoperative vasal fluid showing sperm or sperm heads favors vasovasostomy."
    if epididymal_obstruction or sperm_in_vas is False:
        procedure = "Vasoepididymostomy (VE)"
        procedure_rationale = "Absence of sperm in vasal fluid or epididymal obstruction indicates vasoepididymostomy is required."
        warnings.append("Vasoepididymostomy is technically more demanding; refer to high-volume microsurgeon.")
    rationale.append(procedure_rationale)

    # Partner age
    if partner_age > 37:
        warnings.append(
            f"Partner age {_num_str(partner_age)}: diminished ovarian reserve likely. Consider concurrent IVF/ICSI planning."
        )
        rationale.append(
            "AUA/ASRM guidelines recommend discussing IVF/ICSI as alternative when female partner is >37 years."
        )

    # Anti-sperm antibodies
    if antisperm_antibodies:
        warnings.append("Anti-sperm antibodies detected: may reduce fertilization rates even after successful reversal.")

    # FSH
    if fsh_level > 7.6:
        warnings.append(
            f"Elevated FSH ({_num_str(fsh_level)} mIU/mL) suggests impaired spermatogenesis; reversal success may be reduced."
        )

    # Testis volume
    if testis_volume == "atrophic":
        warnings.append("Testicular atrophy suggests primary spermatogenic failure; reversal may not restore fertility.")
        rationale.append(
            "Testicular atrophy is associated with poor reversal outcomes; sperm banking at time of reversal is strongly recommended."
        )

    # Prior reversal
    if prior_vasectomy_reversal:
        warnings.append("Prior failed reversal: success rates are lower; vasoepididymostomy more likely required.")

    recommendation = (
        "caution"
        if len([w for w in warnings if ("atrophy" in w or "spermatogenic failure" in w)]) > 0
        else "indicated"
    )
    cor = "I" if years_since_vasectomy <= 14 else "IIa"
    loe = "B"

    return {
        "recommendation": recommendation,
        "procedure": procedure,
        "patencyRate": patency_rate,
        "pregnancyRate": pregnancy_rate,
        "cor": cor,
        "loe": loe,
        "warnings": warnings,
        "rationale": rationale,
        "references": references,
    }


def _num_str(x: float) -> str:
    """Render a JS number the way template-literal interpolation would:
    integers without a trailing ``.0`` (e.g. 7 not 7.0)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)
