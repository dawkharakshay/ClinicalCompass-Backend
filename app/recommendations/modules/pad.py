"""PAD Revascularization Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/padLogic.ts
(assessPADRevascularization + all helpers).

Based on: 2024 ACC/AHA/AACVPR/APMA/ABC/SCAI/SVM/SVN/SVS/SIR/VESS Guideline
for the Management of Lower Extremity Peripheral Artery Disease.
Gornik HL et al. J Am Coll Cardiol. 2024;83(24):2497-2604. PMID 38752899
"""

from __future__ import annotations

LOGIC_KEY = "pad"


# ─── Risk Amplifier Assessment ────────────────────────────────────────────────

def assess_risk_amplifiers(input: dict) -> list[str]:
    amplifiers: list[str] = []
    if input.get("diabetes"):
        amplifiers.append("Diabetes mellitus (increased MALE/amputation risk)")
    if input.get("ckd"):
        amplifiers.append("Chronic kidney disease (increased revascularization complication risk)")
    if input.get("eskd"):
        amplifiers.append("End-stage kidney disease (highest amputation/readmission risk after revascularization)")
    if input.get("activeSmoker"):
        amplifiers.append("Active tobacco use (impairs patency, wound healing)")
    if input.get("frailty"):
        amplifiers.append("Frailty (increases surgical revascularization risk)")
    if input.get("heartFailure"):
        amplifiers.append("Heart failure (cilostazol contraindicated; increased perioperative risk)")
    if input.get("severeLungDisease"):
        amplifiers.append("Severe lung disease (increased perioperative risk)")
    if input.get("obesity"):
        amplifiers.append("Obesity (increased surgical complication risk)")
    if input.get("polyvascularDisease"):
        amplifiers.append("Polyvascular disease (increased MACE risk)")
    age = input.get("age")
    if age is not None and age >= 75:
        amplifiers.append("Age >=75 years (increased perioperative risk)")
    return amplifiers


# ─── WIfI Staging ─────────────────────────────────────────────────────────────

def calculate_wifi_stage(wound: int, ischemia: int, foot_infection: int) -> dict:
    total = wound + ischemia + foot_infection
    if total <= 1:
        return {"stage": 1, "label": "Stage 1 (Very Low)", "ampRisk": "<1%", "benefitFromRevasc": "Low"}
    if total <= 3:
        return {"stage": 2, "label": "Stage 2 (Low)", "ampRisk": "1-10%", "benefitFromRevasc": "Moderate"}
    if total <= 6:
        return {"stage": 3, "label": "Stage 3 (Moderate)", "ampRisk": "10-30%", "benefitFromRevasc": "High"}
    return {"stage": 4, "label": "Stage 4 (High)", "ampRisk": ">30%", "benefitFromRevasc": "Very High"}


# ─── Main Assessment Function ─────────────────────────────────────────────────

def assess_pad_revascularization(input: dict) -> dict:
    risk_amplifiers = assess_risk_amplifiers(input)

    subset = input.get("subset")
    if subset == "asymptomatic":
        return _assess_asymptomatic_pad(input, risk_amplifiers)
    if subset == "claudication":
        return _assess_claudication_pad(input, risk_amplifiers)
    if subset == "clti":
        return _assess_clti(input, risk_amplifiers)
    if subset == "ali":
        return _assess_ali(input, risk_amplifiers)
    return _assess_asymptomatic_pad(input, risk_amplifiers)


# ─── Asymptomatic PAD ─────────────────────────────────────────────────────────

def _assess_asymptomatic_pad(input: dict, risk_amplifiers: list[str]) -> dict:
    base_result: dict = {
        "subset": "asymptomatic",
        "subsetLabel": "Asymptomatic PAD",
        "primaryRecommendation": {
            "cor": "3_harm",
            "loe": "B-NR",
            "text": "Revascularization should NOT be performed solely to prevent progression of disease in asymptomatic PAD.",
            "rationale": "No data suggest invasive treatment alters natural history of asymptomatic PAD. Revascularization increases risk of subsequent MALE including need for additional procedures.",
        },
        "additionalRecommendations": [],
        "revascularizationIndicated": False,
        "urgency": "not_indicated",
        "gdmtRequired": True,
        "exerciseTherapyRequired": False,
        "multispecialtyTeamRequired": False,
        "riskAmplifiers": risk_amplifiers,
        "keyMessages": [
            "Focus on guideline-directed medical therapy (GDMT) to reduce MACE and MALE.",
            "Longitudinal follow-up with physical examination is recommended.",
            "Revascularization is not indicated solely to prevent disease progression.",
        ],
    }

    if input.get("otherProcedureNeeded"):
        base_result["revascularizationIndicated"] = True
        base_result["urgency"] = "elective"
        base_result["primaryRecommendation"] = {
            "cor": "2a",
            "loe": "B-NR",
            "text": "Revascularization is reasonable to reconstruct diseased arteries if needed for the safety, feasibility, or effectiveness of other procedures (e.g., TAVR, mechanical circulatory support, EVAR).",
            "rationale": "Endovascular stenting, conduit placement, or other ancillary techniques may be required to facilitate safe sheath insertion/removal for cardiac or vascular procedures.",
        }
        base_result["keyMessages"] = [
            "Revascularization is acceptable when required to facilitate a separate clinically necessary procedure.",
            "Alternative access approaches should be considered to minimize vascular complications.",
            "Revascularization should NOT be performed solely to prevent PAD progression.",
        ]

    return base_result


# ─── Claudication ─────────────────────────────────────────────────────────────

def _assess_claudication_pad(input: dict, risk_amplifiers: list[str]) -> dict:
    gdmt_response = input.get("gdmtResponse")
    functionally_limiting = input.get("functionallyLimiting")
    anatomic_level = input.get("anatomicLevel")
    surgical_risk = input.get("surgicalRisk")

    # GDMT adequate — revascularization not indicated
    if gdmt_response == "adequate":
        return {
            "subset": "claudication",
            "subsetLabel": "Claudication (Chronic Symptomatic PAD)",
            "primaryRecommendation": {
                "cor": "3_no_benefit",
                "loe": "C-EO",
                "text": "Revascularization is NOT recommended in patients with claudication who have had an adequate clinical response to GDMT (including structured exercise).",
                "rationale": "Revascularization carries risk of restenosis, recurrence, MALE, and need for additional procedures. Patients with adequate GDMT response should continue prescribed therapies.",
            },
            "additionalRecommendations": [
                {
                    "cor": "1",
                    "loe": "A",
                    "text": "Continue supervised exercise therapy or structured community-based exercise program.",
                    "rationale": "Improves walking performance, functional status, and quality of life (COR 1, LOE A).",
                }
            ],
            "revascularizationIndicated": False,
            "urgency": "not_indicated",
            "gdmtRequired": True,
            "exerciseTherapyRequired": True,
            "multispecialtyTeamRequired": False,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Patient has had adequate response to GDMT including structured exercise — revascularization is not recommended.",
                "Continue antiplatelet therapy, statin, antihypertensive therapy, and diabetes management.",
                "Longitudinal follow-up to monitor for symptom progression or development of CLTI.",
            ],
        }

    # GDMT not yet tried — optimize first
    if gdmt_response == "not_tried":
        return {
            "subset": "claudication",
            "subsetLabel": "Claudication (Chronic Symptomatic PAD)",
            "primaryRecommendation": {
                "cor": "1",
                "loe": "B-NR",
                "text": "Before revascularization, optimize guideline-directed medical therapy (GDMT) including structured exercise therapy.",
                "rationale": "Revascularization is a second-tier treatment for claudication. GDMT and structured exercise should be optimized first.",
            },
            "additionalRecommendations": [
                {
                    "cor": "1",
                    "loe": "A",
                    "text": "Initiate supervised exercise therapy (SET) or structured community-based exercise program.",
                    "rationale": "SET is recommended to improve walking performance, functional status, and QOL (COR 1, LOE A).",
                },
                {
                    "cor": "1",
                    "loe": "A",
                    "text": "Cilostazol 100 mg twice daily to improve leg symptoms and increase walking distance (if no heart failure).",
                    "rationale": "COR 1, LOE A. Contraindicated in congestive heart failure of any severity.",
                },
            ],
            "revascularizationIndicated": False,
            "urgency": "not_indicated",
            "gdmtRequired": True,
            "exerciseTherapyRequired": True,
            "multispecialtyTeamRequired": False,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "GDMT including structured exercise has not been adequately trialed — optimize before considering revascularization.",
                "Cilostazol is recommended for symptom improvement (contraindicated in heart failure).",
                "Reassess after 3-6 months of GDMT + structured exercise.",
            ],
        }

    # GDMT inadequate — revascularization may be indicated
    if not functionally_limiting:
        return {
            "subset": "claudication",
            "subsetLabel": "Claudication (Chronic Symptomatic PAD)",
            "primaryRecommendation": {
                "cor": "1",
                "loe": "B-NR",
                "text": "Weigh potential benefits (QOL, walking performance) against risks (durability, need for repeat procedures) before revascularization.",
                "rationale": "Shared decision-making is critical. >70% of patients prefer an active role in treatment decisions.",
            },
            "additionalRecommendations": [],
            "revascularizationIndicated": False,
            "urgency": "elective",
            "gdmtRequired": True,
            "exerciseTherapyRequired": True,
            "multispecialtyTeamRequired": False,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Claudication is not functionally limiting — continue GDMT and structured exercise.",
                "Revascularization risk-benefit balance does not favor intervention at this time.",
                "Reassess functional status and QOL at follow-up visits.",
            ],
        }

    # Functionally limiting claudication + inadequate GDMT response — revascularization indicated
    additional_recs: list[dict] = []
    preferred_modality = "endovascular"
    conduit_note: str | None = None

    if anatomic_level in ("aortoiliac", "femoropopliteal", "multilevel"):
        additional_recs.append({
            "cor": "1",
            "loe": "A",
            "text": "Endovascular revascularization is effective for hemodynamically significant aortoiliac or femoropopliteal disease to improve walking performance and QOL.",
            "rationale": "Multiple RCTs demonstrate effectiveness. Long-term patency is greater in aortoiliac than femoropopliteal segment.",
        })
        if surgical_risk == "acceptable":
            additional_recs.append({
                "cor": "2a",
                "loe": "B-NR",
                "text": "Surgical revascularization is reasonable if perioperative risk is acceptable and technical factors suggest advantages over endovascular approaches.",
                "rationale": "COR 2a, LOE B-NR. Consider for complex anatomy, long-segment occlusions, or when endovascular durability is suboptimal.",
            })
            additional_recs.append({
                "cor": "1",
                "loe": "A",
                "text": "If surgical bypass is performed for femoropopliteal disease, use autogenous vein (great saphenous vein) in preference to prosthetic graft.",
                "rationale": "Multiple RCTs show consistent primary patency benefit for autogenous vein vs. prosthetic conduit.",
            })
            conduit_note = "Autogenous vein (GSV) preferred for femoropopliteal bypass. Prosthetic conduit performs well for aortoiliac reconstruction."
        preferred_modality = "endovascular" if surgical_risk == "high" else "endovascular_or_surgical"
    elif anatomic_level == "common_femoral":
        additional_recs.append({
            "cor": "2a",
            "loe": "B-R",
            "text": "Surgical endarterectomy is reasonable for common femoral artery disease, especially if endovascular approaches adversely affect profunda femoris artery pathways.",
            "rationale": "Common femoral endarterectomy has excellent long-term patency (78.5% at 7 years). Preferred when profunda femoris collaterals are at risk.",
        })
        additional_recs.append({
            "cor": "2b",
            "loe": "B-R",
            "text": "Endovascular approaches may be considered in high-risk surgical patients if anatomical factors are favorable (no adverse effect on profunda femoris pathways).",
            "rationale": "COR 2b, LOE B-R. Meta-analytic data show similar 1-year patency but less procedural morbidity vs. endarterectomy.",
        })
        preferred_modality = "endovascular" if surgical_risk == "high" else "endarterectomy"
    elif anatomic_level == "infrapopliteal":
        additional_recs.append({
            "cor": "2b",
            "loe": "C-LD",
            "text": "Effectiveness of endovascular revascularization for isolated infrapopliteal disease in claudication is unknown (no RCTs). Reserved for CLTI.",
            "rationale": "Isolated infrapopliteal disease is an uncommon cause of claudication. Long-term patency of infrapopliteal procedures is lower than aortoiliac/femoropopliteal.",
        })
        additional_recs.append({
            "cor": "2b",
            "loe": "C-LD",
            "text": "Effectiveness of surgical revascularization for isolated infrapopliteal disease in claudication is unknown. Associated with higher perioperative complications vs. popliteal bypass.",
            "rationale": "COR 2b, LOE C-LD. VQI registry data show higher MALE at 1 year for infrapopliteal vs. popliteal bypass in claudication.",
        })
        preferred_modality = "none"

    return {
        "subset": "claudication",
        "subsetLabel": "Claudication (Chronic Symptomatic PAD)",
        "primaryRecommendation": {
            "cor": "2a",
            "loe": "B-R",
            "text": "In patients with functionally limiting claudication and inadequate response to GDMT (including structured exercise), revascularization is a reasonable treatment option to improve walking function and QOL.",
            "rationale": "Multiple RCTs demonstrate effectiveness of revascularization for claudication. Combination of revascularization + supervised exercise outperforms either alone.",
        },
        "additionalRecommendations": additional_recs,
        "revascularizationIndicated": anatomic_level != "infrapopliteal",
        "preferredModality": preferred_modality,
        "urgency": "elective",
        "gdmtRequired": True,
        "exerciseTherapyRequired": True,
        "multispecialtyTeamRequired": False,
        "conduitNote": conduit_note,
        "riskAmplifiers": risk_amplifiers,
        "keyMessages": [
            "Revascularization is a reasonable option for functionally limiting claudication with inadequate GDMT response.",
            "Endovascular therapy is first-line for aortoiliac and femoropopliteal disease.",
            "Combine revascularization with supervised exercise therapy for optimal outcomes.",
            "Shared decision-making is essential — discuss durability, restenosis risk, and need for repeat procedures.",
            "Infrapopliteal revascularization for claudication has uncertain effectiveness — typically reserved for CLTI.",
        ],
    }


# ─── CLTI ─────────────────────────────────────────────────────────────────────

def _assess_clti(input: dict, risk_amplifiers: list[str]) -> dict:
    revascularization_feasible = input.get("revascularizationFeasible")
    clti_presentation = input.get("cltiPresentation")
    conduit_availability = input.get("conduitAvailability")
    surgical_risk = input.get("surgicalRisk")
    cfa_involvement = input.get("cfaInvolvement")
    multilevel_disease = input.get("multilevelDisease")
    wifi_wound = input.get("wifiWound")
    wifi_ischemia = input.get("wifiIschemia")
    wifi_foot_infection = input.get("wifiFootInfection")

    additional_recs: list[dict] = []

    # WIfI staging note
    wifi_note: str | None = None
    if wifi_wound is not None and wifi_ischemia is not None and wifi_foot_infection is not None:
        wifi_result = calculate_wifi_stage(wifi_wound, wifi_ischemia, wifi_foot_infection)
        wifi_note = (
            f"WIfI {wifi_result['label']} — 1-year amputation risk: {wifi_result['ampRisk']}. "
            f"Benefit from revascularization: {wifi_result['benefitFromRevasc']}."
        )

    # No-option CLTI
    if revascularization_feasible is False:
        return {
            "subset": "clti",
            "subsetLabel": "Chronic Limb-Threatening Ischemia (CLTI)",
            "primaryRecommendation": {
                "cor": "1",
                "loe": "C-EO",
                "text": "In patients with CLTI, a patient-centered approach using objective classification (WIfI, GLASS), patient risk, anatomic pattern, and patient/family goals is recommended to identify those for whom primary amputation or palliative management is appropriate.",
                "rationale": "When revascularization is not feasible, local wound management, pain control, and palliative care are the primary options. Primary amputation should only be considered after review by an experienced revascularization specialist.",
            },
            "additionalRecommendations": [
                {
                    "cor": "2b",
                    "loe": "B-R",
                    "text": "Prostanoids may be considered when no other viable treatments are available, particularly for short-term relief of ischemic rest pain (usefulness uncertain).",
                    "rationale": "COR 2b, LOE B-R. Prostanoids reduced ischemic rest pain (RR 1.30) and improved wound healing (RR 1.24) vs. placebo in meta-analysis.",
                },
                {
                    "cor": "2b",
                    "loe": "B-NR",
                    "text": "Arterial intermittent pneumatic compression devices may be considered to augment wound healing or ameliorate ischemic rest pain in no-option CLTI.",
                    "rationale": "COR 2b, LOE B-NR. May reduce minor amputation and improve QOL; does not appear to reduce major amputation.",
                },
                {
                    "cor": "1",
                    "loe": "B-NR",
                    "text": "Multispecialty care team evaluation is required before major amputation (except life-threatening sepsis).",
                    "rationale": "All revascularization and therapeutic options should be evaluated before amputation.",
                },
            ],
            "revascularizationIndicated": False,
            "urgency": "urgent",
            "gdmtRequired": True,
            "exerciseTherapyRequired": False,
            "multispecialtyTeamRequired": True,
            "wifiNote": wifi_note,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Revascularization is not feasible — consider no-option CLTI management strategies.",
                "Multispecialty care team evaluation is mandatory before major amputation.",
                "Use WIfI and GLASS classification to objectively document the no-option patient.",
                "Palliative options include prostanoids, arterial IPC, and pain management.",
                "Primary amputation is indicated when life over limb is the prevailing consideration.",
            ],
        }

    # Revascularization feasible — determine strategy
    additional_recs.append({
        "cor": "1",
        "loe": "B-R",
        "text": "Surgical, endovascular, or hybrid revascularization is recommended when feasible to minimize tissue loss, heal wounds, relieve pain, and preserve a functional limb.",
        "rationale": "Revascularization is the standard treatment for CLTI. Multiple RCTs and meta-analyses support its effectiveness.",
    })

    additional_recs.append({
        "cor": "1",
        "loe": "C-EO",
        "text": "Multispecialty care team evaluation is recommended before amputation.",
        "rationale": "Team-based care optimizes outcomes in CLTI. Includes vascular surgery, IR, podiatry, wound care, endocrinology, and infectious disease.",
    })

    # Conduit and strategy recommendations
    preferred_modality = "endovascular_or_surgical"
    conduit_note: str | None = None

    if conduit_availability == "adequate_gsv":
        additional_recs.append({
            "cor": "1",
            "loe": "A",
            "text": "Bypass to popliteal or infrapopliteal arteries should be constructed with autogenous vein (great saphenous vein) if available.",
            "rationale": "COR 1, LOE A. Autogenous vein provides superior patency for infrainguinal bypass. GSV >=3 mm diameter is the criterion for adequacy (BEST-CLI trial).",
        })
        conduit_note = "Great saphenous vein (GSV) >=3 mm available — autogenous vein bypass is preferred. Vein mapping with duplex ultrasound is recommended."

        if surgical_risk == "acceptable":
            additional_recs.append({
                "cor": "1",
                "loe": "B-R",
                "text": "For infrainguinal CLTI, anatomy, available conduit, patient comorbidities, and patient preferences should guide the choice between surgical bypass and endovascular revascularization (Table 16).",
                "rationale": "BEST-CLI trial (Cohort 1 with adequate GSV): surgical bypass reduced composite of death/MALE vs. endovascular (HR 0.68, p<0.001). BASIL-2 (infrapopliteal disease): endovascular had lower death/amputation vs. bypass.",
            })
            preferred_modality = "surgical_preferred"
        else:
            preferred_modality = "endovascular_preferred"
            additional_recs.append({
                "cor": "1",
                "loe": "B-R",
                "text": "High perioperative risk (cardiac, pulmonary, renal, frailty) may favor endovascular revascularization as the initial strategy.",
                "rationale": "Patient comorbidities are a key factor in revascularization strategy selection (Table 16, 2024 ACC/AHA PAD Guideline).",
            })
    elif conduit_availability == "inadequate_gsv":
        conduit_note = "No suitable GSV available — prosthetic or alternative conduit required for surgical bypass. Absence of suitable autogenous vein may favor endovascular revascularization."
        additional_recs.append({
            "cor": "2a",
            "loe": "B-NR",
            "text": "If surgical approach is selected and suitable autogenous vein is unavailable, prosthetic or cadaveric grafts can be effective for bypass to popliteal and tibial arteries.",
            "rationale": "COR 2a, LOE B-NR. BEST-CLI Cohort 2 (no adequate GSV): no significant difference between endovascular and surgical bypass (HR 0.79, p=0.12).",
        })
        preferred_modality = "endovascular_preferred"

    # Wound/tissue loss specific recommendations
    if clti_presentation in ("minor_tissue_loss", "major_tissue_loss", "combined"):
        additional_recs.append({
            "cor": "2a",
            "loe": "B-NR",
            "text": "Revascularization achieving in-line blood flow or maximizing perfusion to the wound bed (angiosome-directed) can be beneficial for nonhealing wounds or gangrene.",
            "rationale": "Meta-analyses show lowest amputation rates with direct revascularization, intermediate with indirect via collaterals, highest with indirect without collaterals.",
        })

    # Multilevel disease / rest pain
    if clti_presentation == "rest_pain" and multilevel_disease:
        additional_recs.append({
            "cor": "2a",
            "loe": "C-LD",
            "text": "For ischemic rest pain from multilevel arterial disease, a revascularization strategy addressing inflow disease first is reasonable.",
            "rationale": "COR 2a, LOE C-LD. Inflow correction may relieve rest pain; outflow can be addressed subsequently if symptoms persist.",
        })

    # CFA involvement
    if cfa_involvement:
        additional_recs.append({
            "cor": "2a",
            "loe": "B-NR",
            "text": "Lesions involving the common femoral artery and origin of the profunda femoris artery may favor surgical revascularization.",
            "rationale": "Anatomic characteristics favoring surgical approach include CFA/profunda femoris involvement, multilevel chronic total occlusions, and lesions that would adversely impact future surgical bypass options.",
        })

    return {
        "subset": "clti",
        "subsetLabel": "Chronic Limb-Threatening Ischemia (CLTI)",
        "primaryRecommendation": {
            "cor": "1",
            "loe": "B-R",
            "text": "Revascularization (surgical, endovascular, or hybrid) is recommended when feasible to minimize tissue loss, heal wounds, relieve pain, and preserve a functional limb.",
            "rationale": "Revascularization is the standard treatment for CLTI. Goal is to maximize perfusion to the foot and wound bed.",
        },
        "additionalRecommendations": additional_recs,
        "revascularizationIndicated": True,
        "preferredModality": preferred_modality,
        "urgency": "urgent",
        "gdmtRequired": True,
        "exerciseTherapyRequired": False,
        "multispecialtyTeamRequired": True,
        "conduitNote": conduit_note,
        "wifiNote": wifi_note,
        "riskAmplifiers": risk_amplifiers,
        "keyMessages": [
            "Revascularization is the standard of care for CLTI — not the exception.",
            "Multispecialty care team evaluation is essential before amputation.",
            "Conduit availability (GSV >=3 mm) is a key determinant of surgical vs. endovascular strategy.",
            "BEST-CLI: surgical bypass superior in patients with adequate GSV; BASIL-2: endovascular may be preferred for infrapopliteal disease.",
            "Goal of revascularization: in-line blood flow to the foot / angiosome-directed perfusion.",
            "Optimize GDMT, wound care, glycemic control, and infection management concurrently.",
        ],
    }


# ─── Acute Limb Ischemia ──────────────────────────────────────────────────────

def _assess_ali(input: dict, risk_amplifiers: list[str]) -> dict:
    ali_category = input.get("aliCategory")

    if ali_category == "III":
        return {
            "subset": "ali",
            "subsetLabel": "Acute Limb Ischemia (ALI)",
            "primaryRecommendation": {
                "cor": "3_harm",
                "loe": "C-EO",
                "text": "Revascularization of nonviable tissue should NOT be performed. Primary amputation is indicated.",
                "rationale": "Category III ALI represents irreversible damage with inevitable major tissue loss or permanent nerve damage. Revascularization of a nonsalvageable limb is harmful.",
            },
            "additionalRecommendations": [
                {
                    "cor": "1",
                    "loe": "C-EO",
                    "text": "Emergency evaluation by a clinician with sufficient experience to assess limb viability and implement appropriate therapy.",
                    "rationale": "ALI is a vascular emergency. If local expertise is unavailable, immediate patient transfer should be considered.",
                }
            ],
            "revascularizationIndicated": False,
            "preferredModality": "emergency_amputation",
            "urgency": "emergent",
            "gdmtRequired": False,
            "exerciseTherapyRequired": False,
            "multispecialtyTeamRequired": True,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Category III ALI: Nonsalvageable limb — revascularization is contraindicated.",
                "Emergency amputation is the appropriate intervention.",
                "Immediate surgical consultation required.",
            ],
        }

    if ali_category == "IIb":
        return {
            "subset": "ali",
            "subsetLabel": "Acute Limb Ischemia (ALI)",
            "primaryRecommendation": {
                "cor": "1",
                "loe": "C-EO",
                "text": "Category IIb ALI (immediately threatened limb): Immediate revascularization is required if limb salvage is to be accomplished.",
                "rationale": "The category IIb limb is immediately threatened and salvageable only with prompt intervention. Delay risks irreversible ischemic damage.",
            },
            "additionalRecommendations": [
                {
                    "cor": "1",
                    "loe": "C-EO",
                    "text": "Emergency evaluation by experienced clinician. Initiate systemic anticoagulation immediately.",
                    "rationale": "Rapid assessment of limb viability and implementation of therapy is critical. Initial evaluation can be achieved without noninvasive imaging.",
                },
                {
                    "cor": "1",
                    "loe": "C-LD",
                    "text": "Initial clinical evaluation should rapidly assess limb viability without requiring noninvasive imaging (duplex, CTA, MRA) in most cases.",
                    "rationale": "COR 1, LOE C-LD. Treatment for ALI is implemented without additional imaging in most cases.",
                },
            ],
            "revascularizationIndicated": True,
            "preferredModality": "urgent_revascularization",
            "urgency": "emergent",
            "gdmtRequired": False,
            "exerciseTherapyRequired": False,
            "multispecialtyTeamRequired": True,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Category IIb ALI: IMMEDIATELY THREATENED — requires emergent revascularization.",
                "Initiate systemic anticoagulation immediately.",
                "Do not delay for imaging unless complex history of previous revascularization.",
                "Transfer to facility with revascularization expertise if not locally available.",
            ],
        }

    if ali_category == "IIa":
        return {
            "subset": "ali",
            "subsetLabel": "Acute Limb Ischemia (ALI)",
            "primaryRecommendation": {
                "cor": "1",
                "loe": "C-EO",
                "text": "Category IIa ALI (marginally threatened limb): Urgent revascularization is required. Limb is salvageable if promptly treated.",
                "rationale": "Category IIa limb is marginally threatened. Prompt intervention is required to prevent progression to IIb or irreversible ischemia.",
            },
            "additionalRecommendations": [
                {
                    "cor": "1",
                    "loe": "C-EO",
                    "text": "Emergency evaluation by experienced clinician. Initiate systemic anticoagulation.",
                    "rationale": "Rapid assessment and treatment initiation is essential.",
                },
                {
                    "cor": "2b",
                    "loe": "C-EO",
                    "text": "Noninvasive imaging (duplex, CTA, MRA) may be reasonable in patients with complicated history of revascularization procedures before deciding on treatment approach.",
                    "rationale": "COR 2b, LOE C-EO. In most cases, treatment proceeds without imaging.",
                },
            ],
            "revascularizationIndicated": True,
            "preferredModality": "urgent_revascularization",
            "urgency": "urgent",
            "gdmtRequired": False,
            "exerciseTherapyRequired": False,
            "multispecialtyTeamRequired": True,
            "riskAmplifiers": risk_amplifiers,
            "keyMessages": [
                "Category IIa ALI: Marginally threatened — urgent revascularization required.",
                "Initiate systemic anticoagulation immediately.",
                "Imaging may be considered if complex prior revascularization history.",
                "Transfer to facility with revascularization expertise if not locally available.",
            ],
        }

    # Category I — viable, not immediately threatened
    return {
        "subset": "ali",
        "subsetLabel": "Acute Limb Ischemia (ALI)",
        "primaryRecommendation": {
            "cor": "1",
            "loe": "C-EO",
            "text": "Category I ALI (viable limb, not immediately threatened): Urgent evaluation and anticoagulation. Revascularization planning can proceed in a more controlled manner.",
            "rationale": "Category I limb is viable. Anticoagulation is initiated and revascularization planning can be performed with appropriate imaging.",
        },
        "additionalRecommendations": [
            {
                "cor": "1",
                "loe": "C-EO",
                "text": "Emergency evaluation by experienced clinician. Initiate systemic anticoagulation.",
                "rationale": "Even in Category I ALI, prompt evaluation and anticoagulation are required.",
            },
            {
                "cor": "2b",
                "loe": "C-EO",
                "text": "Noninvasive imaging (duplex, CTA, MRA) may be reasonable to guide revascularization planning.",
                "rationale": "Imaging can be obtained in a more controlled manner for Category I ALI.",
            },
        ],
        "revascularizationIndicated": True,
        "preferredModality": "urgent_revascularization",
        "urgency": "urgent",
        "gdmtRequired": False,
        "exerciseTherapyRequired": False,
        "multispecialtyTeamRequired": True,
        "riskAmplifiers": risk_amplifiers,
        "keyMessages": [
            "Category I ALI: Viable limb — initiate anticoagulation and urgent evaluation.",
            "Revascularization planning can proceed with appropriate imaging.",
            "Monitor closely for progression to Category IIa/IIb.",
            "Transfer to facility with revascularization expertise if not locally available.",
        ],
    }


# ─── Utility Functions ────────────────────────────────────────────────────────

def get_cor_label(cor: str) -> str | None:
    return {
        "1": "COR 1 (Strong)",
        "2a": "COR 2a (Moderate)",
        "2b": "COR 2b (Weak)",
        "3_no_benefit": "COR 3: No Benefit",
        "3_harm": "COR 3: Harm",
    }.get(cor)


def get_cor_color(cor: str) -> str | None:
    return {
        "1": "text-green-700 bg-green-50 border-green-200",
        "2a": "text-blue-700 bg-blue-50 border-blue-200",
        "2b": "text-yellow-700 bg-yellow-50 border-yellow-200",
        "3_no_benefit": "text-orange-700 bg-orange-50 border-orange-200",
        "3_harm": "text-red-700 bg-red-50 border-red-200",
    }.get(cor)


def get_urgency_label(urgency: str) -> str | None:
    return {
        "elective": "Elective",
        "urgent": "Urgent",
        "emergent": "Emergent",
        "not_indicated": "Not Indicated",
    }.get(urgency)


def get_urgency_color(urgency: str) -> str | None:
    return {
        "elective": "text-blue-700 bg-blue-50",
        "urgent": "text-orange-700 bg-orange-50",
        "emergent": "text-red-700 bg-red-50",
        "not_indicated": "text-gray-600 bg-gray-50",
    }.get(urgency)


def get_modality_label(modality: str) -> str | None:
    return {
        "endovascular": "Endovascular",
        "surgical_bypass": "Surgical Bypass",
        "endarterectomy": "Surgical Endarterectomy",
        "hybrid": "Hybrid (Endovascular + Surgical)",
        "endovascular_or_surgical": "Endovascular or Surgical",
        "surgical_preferred": "Surgical Bypass Preferred",
        "endovascular_preferred": "Endovascular Preferred",
        "amputation": "Amputation",
        "none": "Not Recommended (Uncertain Effectiveness)",
        "urgent_revascularization": "Urgent Revascularization",
        "emergency_amputation": "Emergency Amputation",
    }.get(modality)


def assess(data: dict) -> dict:
    return assess_pad_revascularization(data)
