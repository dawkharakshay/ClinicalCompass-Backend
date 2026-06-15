"""Gestational Carrier Clinical Compass.

Ported 1:1 from old_static_code/client/src/pages/GestationalCarrierCompass.tsx
(the ``evaluate`` function — logic is inline in the page, no *Logic.ts file).
"""

from __future__ import annotations

from app.recommendations.jslib import truthy

LOGIC_KEY = "gestationalcarrier"

_REFERENCES = [
    "Practice Committee of the ASRM. Recommendations for practices utilizing gestational carriers. Fertil Steril. 2022;118(1):65-74.",
    "Ethics Committee of the ASRM. Using family members as known donors or gestational carriers. Fertil Steril. 2012;98(4):797-803.",
    "ACOG Committee Opinion No. 660. Family Building Through Gestational Surrogacy. Obstet Gynecol. 2016;127(3):e97-e103.",
]


def assess(data: dict) -> dict:
    warnings: list[str] = []
    rationale: list[str] = []
    references = list(_REFERENCES)

    has_medical_indication = (
        truthy(data.get("congenitalAbsenceUterus"))
        or truthy(data.get("surgicalAbsenceUterus"))
        or truthy(data.get("ashermansSyndrome"))
        or truthy(data.get("uterineMalformation"))
        or truthy(data.get("medicalContraindication"))
    )

    has_relative_indication = truthy(data.get("recurrentImplantationFailure")) or truthy(
        data.get("recurrentPregnancyLoss")
    )

    recommendation = "not_indicated"
    procedure = ""
    cor = "I"
    loe = "B"

    if has_medical_indication:
        recommendation = "indicated"
        procedure = "Gestational carrier (surrogacy) — medical indication"
        cor = "I"
        loe = "B"
        if truthy(data.get("congenitalAbsenceUterus")):
            rationale.append(
                "Congenital absence of uterus (MRKH syndrome): gestational carrier is the only option for genetic parenthood."
            )
        if truthy(data.get("surgicalAbsenceUterus")):
            rationale.append(
                "Surgical absence of uterus (hysterectomy): gestational carrier is medically necessary for genetic parenthood."
            )
        if truthy(data.get("ashermansSyndrome")):
            rationale.append(
                "Severe Asherman's syndrome with failed hysteroscopic treatment: uterine factor infertility."
            )
        if truthy(data.get("uterineMalformation")):
            rationale.append(
                "Severe uterine malformation incompatible with pregnancy: gestational carrier is indicated."
            )
        if truthy(data.get("medicalContraindication")):
            detail = data.get("medicalContraindicationDetail")
            detail = detail if truthy(detail) else "documented medical condition"
            rationale.append(f"Medical contraindication to pregnancy: {detail}.")
        warnings.append(
            "Most insurance plans exclude gestational carrier-related procedures. Medical necessity documentation is critical for any coverage appeal."
        )
    elif has_relative_indication:
        recommendation = "consider"
        procedure = "Gestational carrier — relative indication (shared decision-making)"
        cor = "IIb"
        loe = "C"
        rationale.append(
            "Relative indication: recurrent implantation failure or pregnancy loss may have a uterine component. Thorough evaluation before proceeding to gestational carrier."
        )
        warnings.append(
            "Relative indications for gestational carrier are rarely covered by insurance. Absolute uterine factor documentation is required for most coverage appeals."
        )
    else:
        recommendation = "not_indicated"
        procedure = "Gestational carrier — no medical indication identified"
        warnings.append(
            "Social/elective gestational carrier arrangements are almost universally excluded from insurance coverage."
        )

    if not truthy(data.get("carrierIdentified")):
        warnings.append(
            "Gestational carrier not yet identified. ASRM recommends thorough medical, psychological, and legal screening of all carriers."
        )
    if not truthy(data.get("legalAgreementComplete")):
        warnings.append(
            "Legal agreement between intended parents and carrier must be completed before any medical procedures."
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
