"""Embryo Cryopreservation Clinical Compass.

Ported 1:1 from the inline ``evaluate()`` in
old_static_code/client/src/pages/EmbryoCryoCompass.tsx.

No dedicated *Logic.ts file exists for this module — the decision logic lives
inline in the Compass page. There is no server-side .test.ts oracle for this
module, so test fixtures are derived directly from the TS branches.
"""

from __future__ import annotations

from app.recommendations.jslib import num, truthy

LOGIC_KEY = "embryocryo"

_REFERENCES = [
    "Practice Committees of ASRM and SART. Criteria for number of embryos to transfer: a committee opinion. Fertil Steril. 2021;116(3):651-654.",
    "Cobo A, et al. Elective and Onco-fertility Preservation: Factors Related to IVF Outcomes. Hum Reprod. 2018;33(12):2222-2231.",
    "ASRM Practice Committee. Cryopreservation of embryos and oocytes. Fertil Steril. 2013;99(1):37-43.",
    "Oktay K, et al. Fertility Preservation in Patients With Cancer: ASCO Clinical Practice Guideline Update. J Clin Oncol. 2018;36(19):1994-2001.",
]


def _fmt_years(years: float) -> str:
    """Reproduce JS number -> string interpolation (e.g. ``12`` not ``12.0``)."""
    if years == int(years):
        return str(int(years))
    return repr(years)


def assess(data: dict) -> dict:
    indication = data.get("indication")
    gonadotoxic_therapy = truthy(data.get("gonadotoxicTherapy"))
    ovarian_hyperstimulation_risk = truthy(data.get("ovarianHyperstimulationRisk"))
    endometrial_issue = truthy(data.get("endometrialIssue"))
    storage_years = num(data.get("storageYears"), 0)

    warnings: list[str] = []
    rationale: list[str] = []

    recommendation = "indicated"
    procedure = ""
    cor = "I"
    loe = "A"

    if indication == "oncofertility" and gonadotoxic_therapy:
        procedure = "Embryo cryopreservation — oncofertility (medical necessity)"
        cor, loe = "I", "A"
        rationale.append(
            "Gonadotoxic therapy planned: ASCO 2018 guideline recommends embryo cryopreservation as standard of care for fertility preservation before gonadotoxic treatment."
        )
        rationale.append(
            "Embryo cryopreservation has the highest success rates of all fertility preservation methods."
        )
    elif indication == "ivf_excess":
        procedure = "Embryo cryopreservation — excess embryos from IVF cycle"
        cor, loe = "I", "A"
        rationale.append(
            "Excess embryos: cryopreservation of supernumerary embryos is standard practice in IVF. Frozen embryo transfer (FET) cycles have equivalent or superior outcomes to fresh transfers."
        )
        if ovarian_hyperstimulation_risk:
            rationale.append(
                "OHSS risk: freeze-all strategy is indicated to prevent ovarian hyperstimulation syndrome. All embryos should be cryopreserved for deferred transfer."
            )
            warnings.append(
                "Freeze-all strategy recommended: fresh transfer contraindicated with OHSS risk. Deferred FET after ovarian recovery."
            )
        if endometrial_issue:
            rationale.append(
                "Endometrial issue identified: deferred FET allows endometrial optimization before transfer."
            )
    elif indication == "pgt":
        procedure = "Embryo cryopreservation — for PGT biopsy and results"
        cor, loe = "I", "A"
        rationale.append(
            "PGT planned: embryos must be cryopreserved during biopsy and while awaiting genetic results. This is a required step in the PGT process."
        )
    elif indication == "defer_transfer":
        procedure = "Elective embryo cryopreservation — deferred transfer"
        cor, loe = "IIa", "B"
        rationale.append(
            "Elective freeze: patient preference to defer embryo transfer. Frozen embryo transfer outcomes are comparable to fresh transfer."
        )
    else:
        procedure = "Embryo cryopreservation — donor embryo banking"
        cor, loe = "I", "B"
        rationale.append(
            "Donor embryo banking: cryopreservation is required for quarantine period and recipient matching."
        )

    if storage_years > 10:
        warnings.append(
            f"Long-term storage ({_fmt_years(storage_years)} years): discuss embryo disposition options with patient. Annual storage fees are typically not covered by insurance."
        )

    warnings.append(
        "Annual embryo storage fees (CPT 89344) are almost universally excluded from insurance coverage. Patients should budget for self-pay storage costs ($500–$1,000/year)."
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
