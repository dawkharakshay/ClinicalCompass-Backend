"""Peripheral Atherectomy Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/atherectomyLogic.ts
(evaluateAtherectomy).

Note: the legacy logicKey "atherecтomy" carries a Cyrillic homoglyph
(U+0442). LOGIC_KEY here uses the Latin equivalent; the registry normalises
incoming keys so dispatch still matches.
"""

from __future__ import annotations

from app.recommendations.jslib import includes, num, truthy

LOGIC_KEY = "atherectomy"

_REFERENCES = [
    "Norgren L, et al. Inter-Society Consensus for the Management of PAD (TASC II). Eur J Vasc Endovasc Surg. 2007;33(Suppl 1):S1-75.",
    "Conte MS, et al. Global Vascular Guidelines on the Management of Chronic Limb-Threatening Ischemia. J Vasc Surg. 2019;69(6S):3S-125S.",
    "Gerhard-Herman MD, et al. 2016 AHA/ACC Guideline on the Management of Patients with Lower Extremity Peripheral Artery Disease. J Am Coll Cardiol. 2017;69(11):e71-e126.",
    "McKinsey JF, et al. Novel Treatment of Patients with Lower Extremity Ischemia: Use of Percutaneous Atherectomy in 579 Lesions (DEFINITIVE LE). JACC Cardiovasc Interv. 2014;7(12):1346-1355.",
    "Adams GL, et al. Comparison of Endovascular Modalities for Infrapopliteal Lesions Through the LIBERTY 360 Study. Circ Cardiovasc Interv. 2016;9(8):e003467.",
    "Shammas NW, et al. CONFIRM Registries: A Prospective Multicenter Registry of Atherectomy for Peripheral Artery Disease. J Endovasc Ther. 2012;19(4):527-537.",
    "Society of Interventional Radiology (SIR), Outpatient Endovascular and Interventional Society (OEIS), Society for Cardiovascular Angiography and Interventions (SCAI). Joint Evidence-Based Letter on Peripheral Atherectomy Coverage. 2022.",
    "Rocha-Singh KJ, et al. Peripheral Arterial Calcification: Prevalence, Mechanism, Detection, and Clinical Implications. Catheter Cardiovasc Interv. 2014;83(6):E212-E220.",
]


def assess(data: dict) -> dict:
    references = list(_REFERENCES)
    warnings: list[str] = []
    rationale: list[str] = []

    rutherford_category = data.get("rutherfordCategory")
    tasc_class = data.get("tascClass")
    glass_stage = data.get("glassStage")

    # Critical limb ischemia — strongest indication
    is_cli = bool(
        truthy(data.get("criticalLimbIschemiaPresent"))
        or includes(["4", "5", "6"], rutherford_category)
    )

    # Claudication — moderate indication
    is_claudication = includes(["2", "3"], rutherford_category)

    # Asymptomatic — not indicated
    is_asymptomatic = rutherford_category == "0"

    # In-stent restenosis — atherectomy preferred over repeat stenting
    is_isr = data.get("lesionType") == "in_stent_restenosis"

    # Calcified lesion — atherectomy improves drug-coated balloon efficacy
    is_calcified = (
        data.get("calcificationGrade") == "moderate"
        or data.get("calcificationGrade") == "severe"
    )

    # Long lesion — TASC C/D or GLASS II/III
    is_complex_lesion = (
        tasc_class == "C"
        or tasc_class == "D"
        or glass_stage == "II"
        or glass_stage == "III"
    )

    # Medical therapy check
    if not truthy(data.get("medicalTherapyOptimized")):
        warnings.append(
            "Medical therapy (antiplatelet therapy, high-intensity statin, supervised exercise) should be optimized prior to or concurrent with revascularization per ACC/AHA 2016 guidelines."
        )

    if not truthy(data.get("smokingCessationCounseled")):
        warnings.append(
            "Smoking cessation counseling is a Class I recommendation for all patients with symptomatic PAD."
        )

    if truthy(data.get("renalInsufficiency")):
        warnings.append(
            "Renal insufficiency (eGFR < 30 or dialysis): minimize contrast volume, consider CO₂ angiography or IVUS guidance. Pre-hydration per institutional protocol."
        )

    if num(data.get("ankleIndexABI"), 0) < 0.4 and is_cli:
        warnings.append(
            "ABI < 0.4 with CLI: consider multi-level disease assessment. Inflow lesions should be addressed first."
        )

    # Device selection logic
    device_recommendation = "not_indicated"

    if not is_asymptomatic:
        vessel_territory = data.get("vesselTerritory")
        if vessel_territory == "femoropopliteal":
            if is_calcified:
                device_recommendation = "orbital"  # Best evidence for calcified femoropopliteal
                rationale.append(
                    "Orbital atherectomy (OA) is supported by the CONFIRM II registry for calcified femoropopliteal lesions, demonstrating improved luminal gain and reduced dissection rates compared to POBA alone."
                )
            elif is_isr:
                device_recommendation = "laser"
                rationale.append(
                    "Excimer laser atherectomy (ELA) has Level B evidence for in-stent restenosis in the femoropopliteal segment, enabling debulking prior to drug-coated balloon (DCB) therapy."
                )
            else:
                device_recommendation = "directional"
                rationale.append(
                    "Directional atherectomy (DA) with the HawkOne/TurboHawk system demonstrated 84.4% primary patency at 12 months in the DEFINITIVE LE trial for femoropopliteal disease."
                )
        elif vessel_territory == "infrapopliteal":
            device_recommendation = "laser"
            rationale.append(
                "Excimer laser atherectomy (ELA) has the strongest evidence base for infrapopliteal (below-the-knee) disease, with the LACI trial demonstrating limb salvage in 92.5% of CLI patients at 6 months."
            )
        elif vessel_territory == "aortoiliac":
            device_recommendation = "rotational"
            rationale.append(
                "Rotational atherectomy (Rotarex) is appropriate for aortoiliac in-stent restenosis and thrombotic occlusions when surgical risk is prohibitive."
            )

    # Recommendation and COR/LOE
    if is_asymptomatic:
        recommendation = "not_indicated"
        cor = "III"
        loe = "C"
        summary = (
            "Atherectomy is NOT indicated for asymptomatic PAD. No revascularization benefit has been demonstrated in asymptomatic patients."
        )
        rationale.append(
            "ACC/AHA 2016 Class III: Revascularization is not recommended for asymptomatic PAD in the absence of functional impairment or limb threat."
        )
        device_recommendation = "not_indicated"
    elif is_cli:
        recommendation = "indicated"
        cor = "I"
        loe = "B"
        summary = (
            "Peripheral atherectomy is INDICATED for critical limb ischemia (CLI/CLTI) when anatomically feasible and surgical risk is elevated. Atherectomy as an adjunct to angioplasty improves procedural outcomes and reduces the need for stenting in calcified CLI lesions."
        )
        rationale.append(
            "SIR/OEIS/SCAI 2022 Joint Statement: Atherectomy is a covered, evidence-based treatment for CLI/CLTI, supported by LIBERTY 360 data showing comparable limb salvage rates to surgical bypass in appropriately selected patients."
        )
        rationale.append(
            "GLASS Stage " + str(glass_stage) + " / TASC " + str(tasc_class) + " lesion with CLI: atherectomy-facilitated revascularization is appropriate per SVS Global Vascular Guidelines 2019."
        )
        if truthy(data.get("woundPresent")):
            rationale.append(
                "Wound present: revascularization to improve tissue perfusion is a Class I indication. Atherectomy debulking prior to DCB or stenting optimizes vessel preparation."
            )
    elif is_claudication and is_complex_lesion:
        recommendation = "indicated"
        cor = "IIa"
        loe = "B"
        summary = (
            "Peripheral atherectomy is REASONABLE for moderate-to-severe claudication with complex (TASC C/D or GLASS II/III) femoropopliteal or infrapopliteal disease, particularly in calcified or ISR lesions where atherectomy-facilitated vessel preparation improves patency."
        )
        rationale.append(
            "TASC " + str(tasc_class) + " / GLASS Stage " + str(glass_stage) + ": complex anatomy where atherectomy debulking prior to DCB or stenting is supported by Level B evidence (DEFINITIVE LE, CONFIRM registries)."
        )
    elif is_claudication and (is_calcified or is_isr):
        recommendation = "indicated"
        cor = "IIa"
        loe = "B"
        summary = (
            "Peripheral atherectomy is REASONABLE for claudication with calcified or in-stent restenotic lesions where atherectomy-facilitated vessel preparation improves drug-coated balloon efficacy and reduces stent use."
        )
        rationale.append(
            "In-stent restenosis: atherectomy debulking prior to DCB is supported by Level B evidence and endorsed by SIR/OEIS/SCAI 2022 as a covered indication."
            if is_isr
            else "Moderate-to-severe calcification: orbital or directional atherectomy improves luminal gain and reduces dissection, enabling effective DCB delivery per CONFIRM II and DEFINITIVE LE data."
        )
    elif is_claudication:
        recommendation = "consider"
        cor = "IIb"
        loe = "C"
        summary = (
            "Atherectomy MAY BE CONSIDERED for claudication with simple (TASC A/B, GLASS I) lesions when standard angioplasty is expected to be suboptimal due to vessel characteristics. Evidence is limited; shared decision-making with the patient is essential."
        )
        rationale.append(
            "Mild claudication with simple anatomy: POBA or DCB alone is the preferred first-line endovascular approach. Atherectomy may be considered as an adjunct if vessel preparation is needed."
        )
    else:
        recommendation = "not_indicated"
        cor = "III"
        loe = "C"
        summary = (
            "Atherectomy is NOT indicated based on the clinical and anatomic profile provided."
        )
        device_recommendation = "not_indicated"

    return {
        "recommendation": recommendation,
        "cor": cor,
        "loe": loe,
        "deviceRecommendation": device_recommendation,
        "summary": summary,
        "rationale": rationale,
        "warnings": warnings,
        "references": references,
    }
