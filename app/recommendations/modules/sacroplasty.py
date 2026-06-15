"""Sacroplasty appropriateness.

Ported 1:1 from old_static_code/client/src/lib/sacroplastyLogic.ts
(assessSacroplasty).
"""

from __future__ import annotations

from app.recommendations.jslib import num

LOGIC_KEY = "sacroplasty"


def _fmt_num(x: float) -> str:
    """Reproduce JS number-to-string in template literals (no trailing .0)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def assess(data: dict) -> dict:
    contraindications: list[str] = []
    rationale: list[str] = []
    optimization_steps: list[str] = []

    # Absolute contraindications
    if data.get("activeInfection"):
        contraindications.append(
            "Active systemic or local infection — absolute contraindication to sacroplasty"
        )
    if data.get("coagulopathy"):
        contraindications.append(
            "Uncorrected coagulopathy — correct before proceeding (INR <1.5, platelets >50,000)"
        )
    if data.get("sacralNerveCompression"):
        contraindications.append(
            "Sacral nerve root compression with neurologic deficit — surgical decompression required before sacroplasty"
        )
    if data.get("bowelBladderDysfunction"):
        contraindications.append(
            "Bowel or bladder dysfunction — evaluate for sacral nerve involvement; neurosurgical consultation required"
        )
    if data.get("pregnancy"):
        contraindications.append(
            "Pregnancy — defer elective sacroplasty; radiation exposure risk"
        )
    if data.get("allergy"):
        contraindications.append(
            "Known allergy to bone cement (PMMA) or contrast — use alternative cement or premedicate"
        )

    if contraindications:
        return {
            "recommendation": "Sacroplasty Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Absolute contraindication(s) identified — address before proceeding."],
            "contraindications": contraindications,
            "optimizationSteps": ["Resolve contraindication(s) before reassessing candidacy"],
            "denisZoneNote": "",
        }

    vas = num(data.get("vasScore"), 0)
    # fractureWeeks parsed in TS but unused in output logic
    fracture_weeks = num(data.get("fractureAgeWeeks"), 0)  # noqa: F841
    conserv_weeks = num(data.get("conservativeWeeks"), 0)

    cor = "IIb"
    urgency = "Elective"

    denis_zone = data.get("denisZone")
    is_zone1 = denis_zone == "zone1"
    is_zone2 = denis_zone == "zone2"
    is_zone3 = denis_zone == "zone3"

    if (
        (data.get("mriEdema") or data.get("ctFractureLine"))
        and (is_zone1 or is_zone2)
        and vas >= 4
        and conserv_weeks >= 2
        and (data.get("osteoporosis") or data.get("malignancy") or data.get("radiation"))
    ):
        cor = "I"
        urgency = "Pathologic Fracture — Expedited" if data.get("malignancy") else "Appropriate"
        zone_desc = "Zone 1 (sacral ala)" if denis_zone == "zone1" else "Zone 2 (sacral foramina)"
        rationale.append(
            f"Sacral insufficiency fracture — Denis {zone_desc} with imaging-confirmed fracture"
        )
        rationale.append(f"VAS pain score {_fmt_num(vas)}/10 — severe pain supporting intervention")
        if data.get("hShapeFracture"):
            rationale.append(
                "H-shaped (Honda sign) bilateral sacral fracture — sacroplasty provides bilateral stabilization"
            )
        if data.get("bilateral"):
            rationale.append(
                "Bilateral sacral fractures — bilateral sacroplasty recommended for adequate stabilization"
            )
        if data.get("malignancy"):
            rationale.append(
                "Pathologic fracture from malignancy — sacroplasty provides rapid pain relief and structural support"
            )
        if data.get("radiation"):
            rationale.append(
                "Radiation-induced insufficiency fracture — sacroplasty is appropriate for refractory pain"
            )
        rationale.append(
            "Conservative therapy trial completed — sacroplasty is recommended per ACR Appropriateness Criteria"
        )
    elif (data.get("mriEdema") or data.get("ctFractureLine")) and vas >= 3 and conserv_weeks >= 2:
        cor = "IIa"
        urgency = "Reasonable"
        rationale.append(
            "Sacral insufficiency fracture with imaging confirmation and persistent pain after conservative therapy"
        )
        if is_zone3:
            rationale.append(
                "Denis Zone 3 (central canal) — higher risk of cement extravasation into spinal canal; proceed with extreme caution"
            )
            optimization_steps.append(
                "Zone 3 fractures: Neurosurgical consultation recommended; consider alternative pain management"
            )
    elif conserv_weeks < 2:
        cor = "IIb"
        urgency = "Continue Conservative Therapy"
        rationale.append(
            "Conservative therapy trial insufficient — most payers require ≥6 weeks for sacral insufficiency fractures"
        )
        optimization_steps.append(
            "Continue analgesics, physical therapy, and mobility aids for ≥6 weeks"
        )
        optimization_steps.append("Document pain scores and functional status at each visit")
        optimization_steps.append(
            "Calcitonin nasal spray may accelerate fracture healing in osteoporotic insufficiency fractures"
        )
    elif not data.get("mriEdema") and not data.get("ctFractureLine"):
        cor = "IIb"
        urgency = "Imaging Confirmation Required"
        rationale.append("MRI bone marrow edema or CT fracture line not documented")
        optimization_steps.append(
            "Obtain MRI pelvis with STIR sequences to confirm sacral insufficiency fracture and bone marrow edema"
        )
        optimization_steps.append(
            "Bone scan or SPECT-CT can confirm fracture activity if MRI is contraindicated"
        )
    else:
        cor = "IIb"
        urgency = "Insufficient Criteria"
        optimization_steps.append(
            "Document VAS ≥4 and functional impairment (inability to ambulate, transfer, or perform ADLs)"
        )
        optimization_steps.append("Confirm Denis zone classification on imaging")
        optimization_steps.append("Complete ≥6-week conservative therapy trial with documentation")

    # Denis zone note
    if is_zone1:
        denis_zone_note = (
            "Denis Zone 1 (sacral ala, lateral to foramina): Most common site for insufficiency "
            "fractures. Lowest risk for sacroplasty — cement extravasation away from neural structures. "
            "Standard sacroplasty approach."
        )
    elif is_zone2:
        denis_zone_note = (
            "Denis Zone 2 (sacral foramina): Moderate risk — cement extravasation can injure sacral "
            "nerve roots (S1-S4). Use low-viscosity cement with fluoroscopic/CT guidance. Consider "
            "CT-guided approach for precise needle placement."
        )
    elif is_zone3:
        denis_zone_note = (
            "Denis Zone 3 (central sacral canal): Highest risk — cement extravasation can cause cauda "
            "equina syndrome. Sacroplasty is relatively contraindicated; neurosurgical consultation "
            "strongly recommended."
        )
    else:
        denis_zone_note = (
            "Denis zone classification required for procedural planning and risk assessment. Obtain "
            "CT or MRI to classify fracture location relative to sacral foramina."
        )

    if cor == "I":
        recommendation = "Sacroplasty Recommended"
    elif cor == "IIa":
        recommendation = "Sacroplasty Reasonable"
    elif urgency == "Continue Conservative Therapy":
        recommendation = "Continue Conservative Therapy — Sacroplasty Premature"
    elif urgency == "Imaging Confirmation Required":
        recommendation = "MRI/CT Imaging Required Before Proceeding"
    else:
        recommendation = "Insufficient Criteria for Sacroplasty"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "B" if data.get("mriEdema") else "C",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
        "denisZoneNote": denis_zone_note,
    }
