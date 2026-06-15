"""Oocyte Cryopreservation Clinical Compass.

Ported 1:1 from the inline ``evaluate()`` in
old_static_code/client/src/pages/OocyteFreezeCompass.tsx.

There is no standalone *Logic.ts for this module; the decision logic lives
inline in the Compass page. No dedicated TS test exists, so fixtures are
authored from the TS branches.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "oocytefreeze"


def _js_num_str(x: float) -> str:
    """Render a number the way JS string interpolation does (no trailing .0)."""
    if x == int(x):
        return str(int(x))
    return repr(x)

_REFERENCES = [
    "Practice Committees of ASRM and SART. Mature oocyte cryopreservation: a guideline. Fertil Steril. 2013;99(1):37-43.",
    "Oktay K, et al. Fertility Preservation in Patients With Cancer: ASCO Clinical Practice Guideline Update. J Clin Oncol. 2018;36(19):1994-2001.",
    "ACOG Committee Opinion No. 584. Oocyte cryopreservation. Obstet Gynecol. 2014;123(1):221-222.",
    "Cobo A, et al. Oocyte vitrification as an efficient option for elective fertility preservation. Fertil Steril. 2016;105(3):755-764.",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    indication = data.get("indication")
    female_age = num(data.get("femaleAge"), 0)
    therapy_timeline = data.get("therapyTimeline")

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "A"

    if indication == "oncofertility" and truthy(data.get("gonadotoxicTherapy")):
        recommendation = "indicated"
        procedure = "Oocyte cryopreservation — oncofertility (medical indication)"
        cor = "I"
        loe = "A"
        rationale.append(
            "Gonadotoxic therapy planned: ASCO 2018 guideline recommends fertility preservation counseling and referral for all patients of reproductive age before gonadotoxic treatment."
        )
        rationale.append(
            "Oocyte vitrification is no longer considered experimental (ASRM 2013) and is the standard of care for oncofertility."
        )
        if truthy(therapy_timeline):
            warnings.append(
                f"Treatment timeline: {therapy_timeline}. Coordinate with oncology — IVF stimulation typically requires 10–14 days."
            )
    elif indication == "medical" and (
        truthy(data.get("prematureOvarianInsufficiency")) or truthy(data.get("geneticCondition"))
    ):
        recommendation = "indicated"
        procedure = "Oocyte cryopreservation — medical indication (POI/genetic condition)"
        cor = "I"
        loe = "B"
        rationale.append(
            "Medical indication for fertility preservation: premature ovarian insufficiency or genetic condition affecting future fertility."
        )
    elif indication == "elective":
        recommendation = "consider"
        procedure = "Elective oocyte cryopreservation — patient counseling required"
        cor = "IIb"
        loe = "C"
        rationale.append(
            "Elective (social) egg freezing: ASRM does not endorse routine elective egg freezing for the sole purpose of circumventing reproductive aging."
        )
        warnings.append(
            "Insurance coverage for elective egg freezing is rare. Most payers require a medical indication (oncofertility, POI, genetic condition)."
        )
        if female_age >= 38:
            warnings.append(
                f"Age {_js_num_str(female_age)}: success rates decline significantly with age. Discuss realistic expectations — fewer usable eggs per cycle expected."
            )
    else:
        recommendation = "not_indicated"
        procedure = "Oocyte cryopreservation — indication not established"
        rationale.append(
            "No clear medical indication identified. Elective preservation may be appropriate but insurance coverage is unlikely."
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
