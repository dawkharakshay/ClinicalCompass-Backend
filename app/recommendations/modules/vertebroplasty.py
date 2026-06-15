"""Vertebroplasty / Kyphoplasty appropriateness.

Ported 1:1 from old_static_code/client/src/lib/vertebroplastyLogic.ts
(assessVertebroplasty).
"""

from __future__ import annotations

from app.recommendations.jslib import num

LOGIC_KEY = "vertebroplasty"


def _fmt_num(x: float) -> str:
    """Render a number the way JS string interpolation would (no trailing
    ``.0`` for whole numbers)."""
    return str(int(x)) if x == int(x) else str(x)


def assess(data: dict) -> dict:
    contraindications: list[str] = []
    rationale: list[str] = []
    optimization_steps: list[str] = []

    # Absolute contraindications
    if data.get("activeInfection"):
        contraindications.append(
            "Active systemic or local infection — absolute contraindication to vertebral augmentation"
        )
    if data.get("coagulopathy"):
        contraindications.append(
            "Uncorrected coagulopathy — correct INR <1.5 and platelet count >50,000 before proceeding"
        )
    if data.get("spinalCordCompression"):
        contraindications.append(
            "Spinal cord compression from retropulsed fragment — surgical decompression required; vertebroplasty contraindicated"
        )
    if data.get("pregnancy"):
        contraindications.append(
            "Pregnancy — defer elective vertebral augmentation; radiation exposure risk"
        )
    if data.get("allergy"):
        contraindications.append(
            "Known allergy to bone cement (PMMA) or contrast — use alternative cement or premedicate"
        )

    if contraindications:
        return {
            "recommendation": "Vertebral Augmentation Contraindicated",
            "cor": "III",
            "loe": "C",
            "urgency": "Contraindicated",
            "rationale": ["Absolute contraindication(s) identified — address before proceeding."],
            "contraindications": contraindications,
            "optimizationSteps": ["Resolve contraindication(s) before reassessing candidacy"],
            "procedureNote": "",
        }

    vas = num(data.get("vasScore"), 0)
    oswestry = num(data.get("oswestryScore"), 0)  # noqa: F841 (parsed in TS, unused)
    fracture_weeks = num(data.get("fractureAgeWeeks"), 0)
    height_loss = num(data.get("heightLoss"), 0)
    conserv_weeks = num(data.get("conservativeWeeks"), 0)

    cor = "IIb"
    urgency = "Elective"

    mri_edema = data.get("mriEdema")
    ct_fracture_line = data.get("ctFractureLine")
    posterior_wall_intact = data.get("posteriorWallIntact")
    osteoporosis = data.get("osteoporosis")
    malignancy = data.get("malignancy")

    # ACR Appropriateness Criteria: Usually Appropriate
    if (
        mri_edema
        and fracture_weeks <= 6
        and vas >= 4
        and (osteoporosis or malignancy)
        and posterior_wall_intact
    ):
        cor = "I"
        urgency = (
            "Acute Fracture — Expedited"
            if fracture_weeks <= 2
            else "Subacute Fracture — Appropriate"
        )
        rationale.append(
            f"Acute/subacute vertebral compression fracture ({_fmt_num(fracture_weeks)} weeks) with MRI-confirmed bone marrow edema"
        )
        rationale.append(f"VAS pain score {_fmt_num(vas)}/10 — severe pain supporting intervention")
        rationale.append("Posterior vertebral wall intact — safe for vertebral augmentation")
        if malignancy:
            rationale.append(
                "Pathologic fracture from malignancy — vertebral augmentation provides rapid pain relief and structural stabilization"
            )
        else:
            rationale.append(
                "Osteoporotic vertebral compression fracture — ACR Appropriateness Criteria: Usually Appropriate for vertebral augmentation"
            )
        if conserv_weeks < 2:
            rationale.append(
                "Note: Short conservative therapy trial — most payers require ≥2–6 weeks unless pain is refractory or patient is hospitalized"
            )
            optimization_steps.append(
                "Document failed conservative therapy or medical necessity for early intervention"
            )
    elif (
        (mri_edema or ct_fracture_line)
        and fracture_weeks <= 12
        and vas >= 4
        and conserv_weeks >= 2
        and posterior_wall_intact
    ):
        cor = "IIa"
        urgency = "Reasonable"
        rationale.append(
            f"Vertebral compression fracture ({_fmt_num(fracture_weeks)} weeks) with imaging-confirmed fracture"
        )
        rationale.append(f"Conservative therapy trial: {_fmt_num(conserv_weeks)} weeks")
        rationale.append(
            "Vertebral augmentation is reasonable for persistent pain after conservative management"
        )
    elif fracture_weeks > 12 and mri_edema:
        cor = "IIb"
        urgency = "Chronic Fracture with Persistent Edema"
        rationale.append(f"Fracture age {_fmt_num(fracture_weeks)} weeks — chronic fracture")
        rationale.append(
            "MRI bone marrow edema suggests fracture non-union or pseudarthrosis — augmentation may still be beneficial"
        )
        optimization_steps.append(
            "Consider dynamic MRI or SPECT-CT to confirm fracture activity before proceeding"
        )
        optimization_steps.append(
            "Most payers limit coverage to fractures <12 months old with imaging evidence of acuity"
        )
    elif not mri_edema and not ct_fracture_line:
        cor = "IIb"
        urgency = "Imaging Evidence Required"
        rationale.append(
            "MRI bone marrow edema or CT fracture line not documented — imaging confirmation required"
        )
        optimization_steps.append(
            "Obtain MRI with STIR/fat-suppressed sequences to confirm acute fracture and bone marrow edema"
        )
        optimization_steps.append("CT can confirm fracture line if MRI is contraindicated")
    elif conserv_weeks < 2:
        cor = "IIb"
        urgency = "Continue Conservative Therapy"
        rationale.append(
            "Conservative therapy trial insufficient — most payers require ≥2–6 weeks"
        )
        optimization_steps.append(
            "Continue analgesics, bracing, and activity modification for ≥6 weeks"
        )
        optimization_steps.append("Document pain scores and functional status at each visit")
    else:
        cor = "IIb"
        urgency = "Insufficient Criteria"
        optimization_steps.append("Confirm MRI bone marrow edema or CT fracture line")
        optimization_steps.append("Document VAS ≥4 and functional impairment")
        optimization_steps.append("Complete ≥6-week conservative therapy trial")

    if not posterior_wall_intact:
        rationale.append(
            "Posterior vertebral wall compromise — increased risk of cement extravasation; kyphoplasty preferred over vertebroplasty; neurosurgery consultation recommended"
        )

    if height_loss >= 50:
        rationale.append(
            f"Severe vertebral height loss ({_fmt_num(height_loss)}%) — kyphoplasty may restore height better than vertebroplasty"
        )

    if data.get("radiculopathy"):
        optimization_steps.append(
            "Radiculopathy present — evaluate for foraminal compromise; consider nerve root block or surgical decompression if radicular pain predominates"
        )

    # Procedure note
    procedure_type = data.get("procedureType")
    if procedure_type == "kyphoplasty":
        procedure_note = (
            "Kyphoplasty (balloon-assisted): Creates cavity before cement injection, allows height restoration, lower cement extravasation risk. Preferred for: height loss >30%, kyphosis >15°, posterior wall compromise, thoracolumbar junction fractures."
        )
    elif procedure_type == "vertebroplasty":
        procedure_note = (
            "Vertebroplasty: Direct cement injection without balloon. Faster, lower cost, comparable pain relief to kyphoplasty in most RCTs. Preferred for: acute fractures with minimal height loss, malignant fractures requiring rapid stabilization."
        )
    else:
        procedure_note = (
            "Both vertebroplasty and kyphoplasty provide equivalent pain relief (VERTOS II). Kyphoplasty offers potential height restoration and lower extravasation risk at higher cost. Choice depends on fracture morphology, height loss, and operator preference."
        )

    if cor == "I":
        recommendation = "Vertebral Augmentation Recommended"
    elif cor == "IIa":
        recommendation = "Vertebral Augmentation Reasonable"
    elif urgency == "Continue Conservative Therapy":
        recommendation = "Continue Conservative Therapy — Augmentation Premature"
    elif urgency == "Imaging Evidence Required":
        recommendation = "MRI/CT Imaging Required Before Proceeding"
    else:
        recommendation = "Insufficient Criteria for Vertebral Augmentation"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": "A" if (mri_edema and fracture_weeks <= 6) else "B",
        "urgency": urgency,
        "rationale": rationale,
        "contraindications": contraindications,
        "optimizationSteps": optimization_steps,
        "procedureNote": procedure_note,
    }
