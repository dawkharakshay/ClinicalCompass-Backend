"""PAD Clinical Performance & Quality Measures.

Ported 1:1 from old_static_code/client/src/lib/padQMLogic.ts
(assessPADQualityMeasures / scorePADQMMeasure / PAD_QM_MEASURES).

7 Performance Measures (PM-1..PM-7) + 8 Quality Measures (QM-1..QM-8) per the
2026 ACC/AHA Clinical Performance and Quality Measures for PAD (PMID: 41505788).
"""

from __future__ import annotations

from typing import Any

from app.recommendations.jslib import js_round, to_bool

LOGIC_KEY = "padqualitymeasures"

# ─── Measure Definitions ──────────────────────────────────────────────────────

PAD_QM_MEASURES: list[dict] = [
    {
        "id": "PM-1",
        "type": "performance",
        "title": "Ankle-Brachial Index (ABI) Testing",
        "description": "Patients with suspected or established PAD who have ABI testing documented within 12 months of the encounter.",
        "numerator": "Patients with documented ABI measurement within 12 months of the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with a diagnosis of PAD or clinical suspicion of PAD (e.g., exertional leg symptoms, non-healing wound, absent pulses).",
        "exclusions": [
            "Patients for whom ABI testing is clinically inappropriate (e.g., non-compressible vessels, known severe calcification) — clinician-documented exclusion",
            "Patients who decline ABI testing",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "The ABI is the gold-standard non-invasive test for diagnosing PAD. An ABI ≤0.90 is diagnostic of PAD. Consistent documentation ensures appropriate diagnosis and risk stratification.",
        "isNew2026": False,
    },
    {
        "id": "PM-2",
        "type": "performance",
        "title": "Statin Therapy for PAD",
        "description": "Patients with established PAD who are prescribed statin therapy for lipid management and cardiovascular risk reduction.",
        "numerator": "Patients with PAD who are prescribed statin therapy or have documented statin therapy at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD (ABI ≤0.90 or prior lower extremity revascularization or amputation for PAD).",
        "exclusions": [
            "Patients with documented statin intolerance or contraindication (e.g., active liver disease, prior rhabdomyolysis)",
            "Patients who decline statin therapy",
        ],
        "guidelineClass": "1",
        "loe": "A",
        "rationale": "High-intensity statin therapy reduces major adverse cardiovascular events (MACE) and major adverse limb events (MALE) in patients with PAD. Statin use is a Class 1, LOE A recommendation in the 2024 ACC/AHA PAD Guideline.",
        "isNew2026": False,
    },
    {
        "id": "PM-3",
        "type": "performance",
        "title": "Antithrombotic Therapy for PAD",
        "description": "Patients with symptomatic PAD (claudication, CLTI, or prior revascularization) who are prescribed antithrombotic therapy (antiplatelet or anticoagulant).",
        "numerator": "Patients with symptomatic PAD who are prescribed antiplatelet therapy (aspirin, clopidogrel, or low-dose rivaroxaban + aspirin) or therapeutic anticoagulation.",
        "denominator": "All patients aged ≥18 years with symptomatic PAD (claudication, CLTI, or prior lower extremity revascularization).",
        "exclusions": [
            "Patients with documented contraindication to antithrombotic therapy (e.g., active major bleeding, severe thrombocytopenia)",
            "Patients who decline antithrombotic therapy",
        ],
        "guidelineClass": "1",
        "loe": "A",
        "rationale": "Antithrombotic therapy (single antiplatelet or low-dose rivaroxaban + aspirin) reduces MACE and MALE in symptomatic PAD. This is a Class 1 recommendation in the 2024 ACC/AHA PAD Guideline.",
        "isNew2026": True,
    },
    {
        "id": "PM-4",
        "type": "performance",
        "title": "Blood Pressure Management",
        "description": "Patients with PAD and hypertension who have blood pressure measured and documented with a management plan targeting SBP <130 mmHg.",
        "numerator": "Patients with PAD and hypertension who have documented blood pressure measurement AND a documented management plan (pharmacotherapy or lifestyle modification) at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD and a diagnosis of hypertension.",
        "exclusions": [
            "Patients for whom blood pressure management is clinically inappropriate (clinician-documented)",
            "Patients who decline blood pressure management",
        ],
        "guidelineClass": "1",
        "loe": "A",
        "rationale": "Hypertension is a major modifiable risk factor for PAD progression and cardiovascular events. Target SBP <130 mmHg is consistent with the 2024 ACC/AHA PAD Guideline and 2017 ACC/AHA Hypertension Guideline.",
        "isNew2026": True,
    },
    {
        "id": "PM-5",
        "type": "performance",
        "title": "ACE Inhibitor / ARB Therapy",
        "description": "Patients with symptomatic PAD who are prescribed ACE inhibitor or ARB therapy for cardiovascular risk reduction.",
        "numerator": "Patients with symptomatic PAD who are prescribed an ACE inhibitor or ARB at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with symptomatic PAD (claudication, CLTI, or prior revascularization).",
        "exclusions": [
            "Patients with documented contraindication to ACE inhibitors and ARBs (e.g., bilateral renal artery stenosis, prior angioedema, pregnancy, hyperkalemia)",
            "Patients who decline ACE inhibitor/ARB therapy",
        ],
        "guidelineClass": "1",
        "loe": "A",
        "rationale": "ACE inhibitors and ARBs reduce cardiovascular mortality and MACE in patients with PAD. Ramipril demonstrated a 22% relative risk reduction in cardiovascular events in the HOPE trial. This is a Class 1, LOE A recommendation.",
        "isNew2026": True,
    },
    {
        "id": "PM-6",
        "type": "performance",
        "title": "Tobacco Use Screening and Cessation Counseling",
        "description": "Patients with PAD who are screened for tobacco use, and if current users, are offered cessation counseling and pharmacotherapy.",
        "numerator": "Patients with PAD who are screened for tobacco use AND, if current users, are offered cessation counseling and pharmacotherapy (varenicline, bupropion, or NRT).",
        "denominator": "All patients aged ≥18 years with established PAD.",
        "exclusions": [
            "Patients who decline tobacco screening",
            "Patients who decline cessation counseling or pharmacotherapy (if current users)",
        ],
        "guidelineClass": "3_harm",
        "loe": "A",
        "rationale": "Tobacco use is the most powerful modifiable risk factor for PAD incidence, progression, and limb loss. Continued smoking after revascularization dramatically worsens outcomes. Cessation counseling + pharmacotherapy is Class 3 (Harm) for continued smoking — meaning continued tobacco use is harmful. PM-6 does NOT have the general clinician-appropriateness exclusion.",
        "isNew2026": False,
    },
    {
        "id": "PM-7",
        "type": "performance",
        "title": "Supervised Exercise Therapy (SET) Referral",
        "description": "Patients with claudication symptoms who are referred to or enrolled in a supervised exercise therapy (SET) program.",
        "numerator": "Patients with claudication who have a documented referral to or enrollment in a supervised exercise therapy program.",
        "denominator": "All patients aged ≥18 years with PAD and claudication symptoms.",
        "exclusions": [
            "Patients who decline supervised exercise therapy referral",
            "Patients with CLTI (rest pain, tissue loss) — SET is not indicated for CLTI",
        ],
        "guidelineClass": "1",
        "loe": "A",
        "rationale": "Supervised exercise therapy is the most effective non-invasive treatment for claudication, improving walking distance, quality of life, and cardiovascular outcomes. It is a Class 1, LOE A recommendation and is Medicare-covered for symptomatic PAD. PM-7 does NOT have the general clinician-appropriateness exclusion.",
        "isNew2026": False,
    },
    {
        "id": "QM-1",
        "type": "quality",
        "title": "Diabetes Management in PAD",
        "description": "Patients with PAD and diabetes mellitus who have HbA1c measured and a documented diabetes management plan.",
        "numerator": "Patients with PAD and diabetes who have documented HbA1c measurement AND a diabetes management plan (pharmacotherapy or referral to endocrinology/diabetes educator) at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD and a diagnosis of diabetes mellitus.",
        "exclusions": [
            "Patients for whom diabetes management is clinically inappropriate (clinician-documented)",
            "Patients who decline diabetes management",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "Diabetes is a major risk factor for PAD severity, wound healing failure, and amputation. HbA1c target <7% (or individualized) reduces microvascular and macrovascular complications. This is a new 2026 measure reflecting the growing importance of cardiometabolic risk management in PAD.",
        "isNew2026": True,
    },
    {
        "id": "QM-2",
        "type": "quality",
        "title": "Preventive Foot Care",
        "description": "Patients with PAD and diabetes or CLTI who receive preventive foot care education and examination.",
        "numerator": "Patients with PAD and diabetes or CLTI who have documented foot examination AND foot care education (self-inspection, footwear, wound prevention) at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD and either diabetes mellitus or CLTI (rest pain, ischemic ulcer, or gangrene).",
        "exclusions": [
            "Patients for whom foot care is clinically inappropriate (clinician-documented)",
            "Patients who decline foot care education or examination",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "Foot complications (ulceration, infection, gangrene) are the leading cause of amputation in patients with PAD and diabetes. Preventive foot care reduces amputation rates. This is a new 2026 quality measure.",
        "isNew2026": True,
    },
    {
        "id": "QM-3",
        "type": "quality",
        "title": "Novel Lipid-Lowering Therapy Consideration",
        "description": "Patients with PAD and LDL-C above goal despite maximally tolerated statin therapy who are considered for novel lipid-lowering agents (PCSK9 inhibitors, inclisiran, bempedoic acid, ezetimibe).",
        "numerator": "Patients with PAD, LDL-C ≥70 mg/dL despite maximally tolerated statin therapy, who have documented consideration of or prescription for novel lipid-lowering agents.",
        "denominator": "All patients aged ≥18 years with established PAD and LDL-C ≥70 mg/dL despite maximally tolerated statin therapy.",
        "exclusions": [
            "Patients for whom novel lipid-lowering therapy is clinically inappropriate (clinician-documented)",
            "Patients who decline novel lipid-lowering therapy",
        ],
        "guidelineClass": "2a",
        "loe": "B-R",
        "rationale": "PCSK9 inhibitors (evolocumab, alirocumab) reduce MACE in high-risk PAD patients. Bempedoic acid and inclisiran are additional options for statin-intolerant patients. LDL-C <70 mg/dL is the target for very high-risk PAD. This is a new 2026 quality measure reflecting emerging evidence.",
        "isNew2026": True,
    },
    {
        "id": "QM-4",
        "type": "quality",
        "title": "Health Disparities Assessment",
        "description": "Patients with PAD who have race/ethnicity, social determinants of health (SDOH), and access-to-care barriers documented to evaluate disparities in PAD detection and management.",
        "numerator": "Patients with PAD who have documented race/ethnicity AND at least one SDOH domain (e.g., food insecurity, housing instability, transportation barriers, insurance status) at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD.",
        "exclusions": [
            "Patients who decline to provide race/ethnicity or SDOH information",
        ],
        "guidelineClass": "1",
        "loe": "C-LD",
        "rationale": "Black, Hispanic, and low-income patients have significantly higher rates of PAD, amputation, and mortality. Systematic documentation of disparities enables targeted quality improvement. This is a new 2026 quality measure reflecting the ACC/AHA's commitment to health equity.",
        "isNew2026": True,
    },
    {
        "id": "QM-5",
        "type": "quality",
        "title": "Saphenous Vein Assessment Prior to Revascularization",
        "description": "Patients undergoing lower extremity surgical revascularization who have preoperative saphenous vein mapping documented.",
        "numerator": "Patients undergoing lower extremity bypass surgery who have documented preoperative duplex ultrasound saphenous vein mapping.",
        "denominator": "All patients aged ≥18 years with PAD undergoing lower extremity bypass surgery (femoral-popliteal or femoral-tibial bypass).",
        "exclusions": [
            "Patients undergoing endovascular-only revascularization (no bypass surgery planned)",
            "Emergency revascularization for acute limb ischemia where preoperative mapping is not feasible",
            "Patients for whom vein mapping is clinically inappropriate (clinician-documented)",
            "Patients who decline vein mapping",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "Autologous saphenous vein is the preferred conduit for infrainguinal bypass. Preoperative vein mapping identifies suitable conduit, reduces operative time, and improves patency rates. This is a new 2026 quality measure.",
        "isNew2026": True,
    },
    {
        "id": "QM-6",
        "type": "quality",
        "title": "Multidisciplinary Team Discussion for CLTI",
        "description": "Patients with CLTI who have a documented multidisciplinary team discussion of treatment options (revascularization vs. primary amputation vs. medical management) prior to definitive treatment.",
        "numerator": "Patients with CLTI who have documented multidisciplinary team discussion (involving at minimum vascular surgery or IR and wound care or podiatry) prior to definitive treatment.",
        "denominator": "All patients aged ≥18 years with CLTI (rest pain, ischemic ulcer, or gangrene) being considered for revascularization or amputation.",
        "exclusions": [
            "Patients with acute limb ischemia requiring emergency revascularization",
            "Patients for whom multidisciplinary discussion is not feasible (e.g., rural setting without specialist access) — clinician-documented",
            "Patients who decline multidisciplinary evaluation",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "CLTI is associated with 30% 1-year mortality and 25% major amputation rate. Multidisciplinary team discussions improve limb salvage rates and reduce unnecessary amputations. The BEST-CLI trial demonstrated that surgical bypass with adequate conduit is superior to endovascular therapy in good surgical candidates. This is a new 2026 quality measure.",
        "isNew2026": True,
    },
    {
        "id": "QM-7",
        "type": "quality",
        "title": "Shared Decision-Making Documentation",
        "description": "Patients with PAD who have documented shared decision-making discussion of treatment risks, benefits, and patient preferences.",
        "numerator": "Patients with PAD who have documented shared decision-making discussion (including patient preferences, treatment options, risks/benefits) at the qualifying encounter.",
        "denominator": "All patients aged ≥18 years with established PAD being considered for revascularization or major medical therapy change.",
        "exclusions": [
            "Emergency revascularization for acute limb ischemia",
            "Patients for whom shared decision-making is not feasible (e.g., altered mental status) — clinician-documented",
        ],
        "guidelineClass": "1",
        "loe": "C-LD",
        "rationale": "Patient-centered care requires that treatment decisions align with patient values and preferences. Shared decision-making improves treatment adherence, patient satisfaction, and outcomes. The 2024 ACC/AHA PAD Guideline emphasizes shared decision-making throughout.",
        "isNew2026": False,
    },
    {
        "id": "QM-8",
        "type": "quality",
        "title": "Post-Revascularization Surveillance",
        "description": "Patients who have undergone lower extremity revascularization who have documented post-procedural surveillance (ABI + duplex ultrasound) within 30 days and at 6 months.",
        "numerator": "Patients who underwent lower extremity revascularization who have documented ABI measurement AND duplex ultrasound within 30 days of the procedure.",
        "denominator": "All patients aged ≥18 years who underwent lower extremity revascularization (endovascular or surgical) within the measurement period.",
        "exclusions": [
            "Patients for whom post-revascularization surveillance is clinically inappropriate (clinician-documented)",
            "Patients who decline post-revascularization surveillance",
        ],
        "guidelineClass": "1",
        "loe": "B-NR",
        "rationale": "Post-revascularization surveillance detects restenosis, occlusion, or graft failure early, enabling timely re-intervention and improving long-term patency. ABI + duplex ultrasound is the standard surveillance protocol per the 2024 ACC/AHA PAD Guideline.",
        "isNew2026": False,
    },
]


# ─── Input helpers (JS-semantics) ─────────────────────────────────────────────


def _b(data: dict, key: str) -> bool:
    """Boolean field — JS truthiness of a submitted form value (default false)."""
    return to_bool(data.get(key))


def _present(data: dict, key: str) -> bool:
    """JS ``input.x !== undefined`` — key present with a non-None value."""
    return data.get(key) is not None


def _numval(data: dict, key: str):
    """Optional numeric field; returns float or None if missing/None."""
    v = data.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _derive_presentation_flags(data: dict) -> dict:
    """Reproduce the legacy form's PAD-Presentation-derived booleans.

    In the old React form (PADQualityMeasures.tsx) choosing a PAD Presentation
    button auto-set ``claudicationSymptoms`` and ``cltiDiagnosis`` — the user
    could never set them independently, so they were always equal to
    ``padPresentation === "claudication"`` / ``=== "clti"``. The generic seeded
    form only submits ``padPresentation``, so without this the claudication- and
    CLTI-dependent measures (notably PM-7 SET referral, plus QM-2/6/7) would
    silently drop to Not Applicable and the assessment would diverge from the
    legacy app. Derive the flags only when a caller has not supplied them, so the
    engine still accepts them as explicit inputs (preserving the port contract).
    """
    pres = data.get("padPresentation")
    if data.get("claudicationSymptoms") is None:
        data["claudicationSymptoms"] = pres == "claudication"
    if data.get("cltiDiagnosis") is None:
        data["cltiDiagnosis"] = pres == "clti"
    return data


def _derive_numeric_flags(data: dict) -> dict:
    """Reproduce the legacy form's number-input-derived booleans.

    In the old React form (PADQualityMeasures.tsx) entering ``systolicBP`` ran
    ``bpGoalAchieved = v !== undefined && v < 130`` and entering ``ldlcValue`` ran
    ``ldlcAtGoal = v !== undefined && v < 70`` — so whenever the numeric value was
    present these booleans were derived from it, never set independently. The
    generic seeded form instead surfaces ``bpGoalAchieved`` / ``ldlcAtGoal`` as
    standalone switches defaulting to False, so a clinician who types an in-goal
    SBP (e.g. 125) without also flipping the toggle would get PM-4 reporting
    "Goal SBP <130 mmHg NOT yet achieved" where the legacy app reported it
    achieved. Mirror the legacy onChange: when the numeric field is supplied,
    derive the flag from it (overriding the seeded default) so the assessment
    matches the old app. See [[module-form-derived-fields]].
    """
    sbp = _numval(data, "systolicBP")
    if sbp is not None:
        data["bpGoalAchieved"] = sbp < 130
    ldlc = _numval(data, "ldlcValue")
    if ldlc is not None:
        data["ldlcAtGoal"] = ldlc < 70
    return data


# ─── Scoring Engine ───────────────────────────────────────────────────────────


def score_pad_qm_measure(measure: dict, data: dict) -> dict:
    eligible = False
    passed = False
    excluded = False
    exclusion_reason: Any = None
    details = ""

    mid = measure["id"]
    pad_presentation = data.get("padPresentation")

    if mid == "PM-1":
        # ABI Testing
        eligible = (
            pad_presentation is not None
            and (
                _b(data, "hasAtherosclerosis")
                or pad_presentation == "claudication"
                or pad_presentation == "clti"
                or pad_presentation == "ali"
            )
        )
        if not eligible:
            details = "Patient does not meet denominator criteria (no PAD diagnosis or suspicion)."
        else:
            abi_measured = _b(data, "abiMeasured")
            abi_documented = _b(data, "abiDocumented")
            if abi_measured is False and abi_documented is False:
                excluded = False
                passed = False
                details = "ABI testing not documented within 12 months. Measure FAILS."
            elif abi_documented:
                passed = True
                aai = data.get("ankleArmIndex")
                aai_str = aai if aai is not None else "on file"
                details = f"ABI documented (value: {aai_str}). Measure PASSES."
            else:
                passed = False
                details = "ABI measured but not documented in chart. Measure FAILS."

    elif mid == "PM-2":
        # Statin Therapy
        eligible = _b(data, "hasAtherosclerosis")
        if not eligible:
            details = "Patient does not have established PAD diagnosis."
        elif _b(data, "statinContraindicated"):
            excluded = True
            exclusion_reason = "Statin therapy contraindicated (documented intolerance or contraindication)."
            details = exclusion_reason
        elif _b(data, "statinDeclined"):
            excluded = True
            exclusion_reason = "Patient declined statin therapy."
            details = exclusion_reason
        else:
            passed = _b(data, "statinPrescribed") or _b(data, "onStatinOrLipidLowering")
            details = (
                "Statin therapy prescribed or documented. Measure PASSES."
                if passed
                else "Statin therapy not prescribed and not documented. Measure FAILS."
            )

    elif mid == "PM-3":
        # Antithrombotic Therapy
        eligible = (
            pad_presentation == "claudication"
            or pad_presentation == "clti"
            or _b(data, "hadRevascularization")
        )
        if not eligible:
            details = "Patient does not have symptomatic PAD or prior revascularization."
        elif _b(data, "antithromboticContraindicated"):
            excluded = True
            exclusion_reason = "Antithrombotic therapy contraindicated (documented)."
            details = exclusion_reason
        elif _b(data, "antithromboticDeclined"):
            excluded = True
            exclusion_reason = "Patient declined antithrombotic therapy."
            details = exclusion_reason
        else:
            passed = _b(data, "antithromboticTherapyPrescribed") or _b(
                data, "onAntiplateletOrAnticoagulant"
            )
            details = (
                "Antithrombotic therapy prescribed or documented. Measure PASSES."
                if passed
                else "Antithrombotic therapy not prescribed and not documented. Measure FAILS."
            )

    elif mid == "PM-4":
        # Blood Pressure Management
        eligible = _b(data, "hasAtherosclerosis") and _b(data, "hasHypertension")
        if not eligible:
            details = "Patient does not have both PAD and hypertension."
        elif _b(data, "bpManagementContraindicated"):
            excluded = True
            exclusion_reason = "BP management contraindicated (documented)."
            details = exclusion_reason
        elif _b(data, "bpManagementDeclined"):
            excluded = True
            exclusion_reason = "Patient declined BP management."
            details = exclusion_reason
        else:
            bp_measured = _b(data, "bpMeasured")
            passed = bp_measured and _b(data, "bpManagementDocumented")
            if passed and _present(data, "systolicBP"):
                goal = (
                    "Goal SBP <130 mmHg achieved."
                    if _b(data, "bpGoalAchieved")
                    else "Goal SBP <130 mmHg NOT yet achieved — intensify therapy."
                )
                details = (
                    f"BP measured (SBP: {data.get('systolicBP')} mmHg) and management documented. "
                    f"{goal} Measure PASSES."
                )
            elif passed:
                details = "BP measured and management documented. Measure PASSES."
            else:
                reason = "not measured" if not bp_measured else "measured but management not documented"
                details = f"BP {reason}. Measure FAILS."

    elif mid == "PM-5":
        # ACE Inhibitor / ARB
        eligible = (
            pad_presentation == "claudication"
            or pad_presentation == "clti"
            or _b(data, "hadRevascularization")
        )
        if not eligible:
            details = "Patient does not have symptomatic PAD."
        elif _b(data, "aceInhibitorContraindicated"):
            excluded = True
            exclusion_reason = "ACE inhibitor/ARB contraindicated (documented)."
            details = exclusion_reason
        elif _b(data, "aceInhibitorDeclined"):
            excluded = True
            exclusion_reason = "Patient declined ACE inhibitor/ARB therapy."
            details = exclusion_reason
        else:
            passed = _b(data, "aceInhibitorPrescribed") or _b(data, "onACEInhibitorOrARB")
            details = (
                "ACE inhibitor or ARB prescribed or documented. Measure PASSES."
                if passed
                else "ACE inhibitor/ARB not prescribed and not documented. Measure FAILS."
            )

    elif mid == "PM-6":
        # Tobacco Use Screening — NO general clinician-appropriateness exclusion
        eligible = _b(data, "hasAtherosclerosis")
        if not eligible:
            details = "Patient does not have established PAD."
        elif not _b(data, "tobaccoUseScreened"):
            passed = False
            details = "Tobacco use screening not documented. Measure FAILS."
        elif not _b(data, "tobaccoUser"):
            passed = True
            details = "Tobacco use screened — patient is a non-user. Measure PASSES."
        else:
            counseling = _b(data, "cessationCounselingProvided")
            passed = counseling and _b(data, "cessationPharmacotherapyOffered")
            if passed:
                details = "Tobacco use screened, patient is a current user, cessation counseling AND pharmacotherapy offered. Measure PASSES."
            else:
                reason = (
                    "cessation counseling not documented"
                    if not counseling
                    else "cessation pharmacotherapy not offered"
                )
                details = f"Tobacco use screened, patient is a current user, but {reason}. Measure FAILS."

    elif mid == "PM-7":
        # Supervised Exercise Therapy — NO general clinician-appropriateness exclusion
        eligible = _b(data, "claudicationSymptoms") and pad_presentation == "claudication"
        if not eligible:
            details = "Patient does not have claudication symptoms (SET is not indicated for CLTI or asymptomatic PAD)."
        elif _b(data, "exerciseTherapyDeclined"):
            excluded = True
            exclusion_reason = "Patient declined supervised exercise therapy referral."
            details = exclusion_reason
        else:
            passed = _b(data, "exerciseTherapyReferralMade")
            details = (
                "Supervised exercise therapy referral documented. Measure PASSES."
                if passed
                else "Supervised exercise therapy referral not documented. Measure FAILS."
            )

    elif mid == "QM-1":
        # Diabetes Management
        eligible = _b(data, "hasAtherosclerosis") and _b(data, "hasDiabetes")
        if not eligible:
            details = "Patient does not have both PAD and diabetes mellitus."
        elif _b(data, "diabetesManagementContraindicated"):
            excluded = True
            exclusion_reason = "Diabetes management contraindicated (documented)."
            details = exclusion_reason
        elif _b(data, "diabetesManagementDeclined"):
            excluded = True
            exclusion_reason = "Patient declined diabetes management."
            details = exclusion_reason
        else:
            hba1c_measured = _b(data, "hba1cMeasured")
            passed = hba1c_measured and _b(data, "diabetesManagementDocumented")
            hba1c_value = _numval(data, "hba1cValue")
            if passed and _present(data, "hba1cValue"):
                note = (
                    "HbA1c above target — intensify management."
                    if (hba1c_value is not None and hba1c_value > 7)
                    else "HbA1c at or below 7% target."
                )
                details = (
                    f"HbA1c measured ({data.get('hba1cValue')}%) and management documented. "
                    f"{note} Measure PASSES."
                )
            elif passed:
                details = "HbA1c measured and diabetes management documented. Measure PASSES."
            else:
                reason = (
                    "HbA1c not measured"
                    if not hba1c_measured
                    else "HbA1c measured but management not documented"
                )
                details = f"{reason}. Measure FAILS."

    elif mid == "QM-2":
        # Preventive Foot Care
        eligible = _b(data, "hasAtherosclerosis") and (
            _b(data, "hasDiabetes") or _b(data, "cltiDiagnosis") or _b(data, "hasFootRisk")
        )
        if not eligible:
            details = "Patient does not have PAD with diabetes, CLTI, or high foot risk."
        elif _b(data, "footCareContraindicated"):
            excluded = True
            exclusion_reason = "Foot care contraindicated (documented)."
            details = exclusion_reason
        elif _b(data, "footCareDeclined"):
            excluded = True
            exclusion_reason = "Patient declined foot care education/examination."
            details = exclusion_reason
        else:
            passed = _b(data, "preventiveFootCareProvided")
            details = (
                "Preventive foot care education and examination documented. Measure PASSES."
                if passed
                else "Preventive foot care not documented. Measure FAILS."
            )

    elif mid == "QM-3":
        # Novel Lipid-Lowering Therapy
        ldlc_value = _numval(data, "ldlcValue")
        eligible = (
            _b(data, "hasAtherosclerosis")
            and not _b(data, "ldlcAtGoal")
            and _present(data, "ldlcValue")
            and (ldlc_value is not None and ldlc_value >= 70)
        )
        if not eligible:
            details = "Patient does not meet criteria (PAD with LDL-C ≥70 mg/dL despite statin therapy)."
        else:
            passed = _b(data, "novelLipidAgentConsidered") or _b(data, "onNovelLipidAgent")
            if passed:
                details = f"Novel lipid-lowering agent considered or prescribed (LDL-C: {data.get('ldlcValue')} mg/dL). Measure PASSES."
            else:
                details = f"LDL-C {data.get('ldlcValue')} mg/dL above goal (≥70 mg/dL) — novel lipid-lowering agent not considered. Measure FAILS."

    elif mid == "QM-4":
        # Health Disparities Assessment
        eligible = _b(data, "hasAtherosclerosis")
        if not eligible:
            details = "Patient does not have established PAD."
        else:
            race_documented = _b(data, "raceEthnicityDocumented")
            passed = race_documented and _b(data, "socialDeterminantsDocumented")
            if passed:
                details = "Race/ethnicity and social determinants of health documented. Measure PASSES."
            else:
                reason = (
                    "Race/ethnicity not documented"
                    if not race_documented
                    else "Race/ethnicity documented but SDOH not documented"
                )
                details = f"{reason}. Measure FAILS."

    elif mid == "QM-5":
        # Saphenous Vein Assessment
        eligible = _b(data, "hadRevascularization") and (
            data.get("revascularizationType") == "surgical"
        )
        if not eligible:
            details = "Patient did not undergo surgical bypass revascularization."
        elif not _present(data, "saphenousVeinAssessedPreOp"):
            passed = False
            details = "Preoperative saphenous vein mapping not documented. Measure FAILS."
        else:
            passed = data.get("saphenousVeinAssessedPreOp") is True
            details = (
                "Preoperative saphenous vein mapping documented. Measure PASSES."
                if passed
                else "Preoperative saphenous vein mapping not performed or not documented. Measure FAILS."
            )

    elif mid == "QM-6":
        # Multidisciplinary Team Discussion for CLTI
        eligible = _b(data, "cltiDiagnosis")
        if not eligible:
            details = "Patient does not have CLTI (rest pain, ischemic ulcer, or gangrene)."
        elif pad_presentation == "ali":
            excluded = True
            exclusion_reason = "Acute limb ischemia requiring emergency revascularization — multidisciplinary discussion not feasible."
            details = exclusion_reason
        else:
            passed = _b(data, "multidisciplinaryDiscussionDocumented") and _b(
                data, "multidisciplinaryTeamInvolved"
            )
            details = (
                "Multidisciplinary team discussion documented prior to definitive treatment. Measure PASSES."
                if passed
                else "Multidisciplinary team discussion not documented. Measure FAILS."
            )

    elif mid == "QM-7":
        # Shared Decision-Making
        eligible = _b(data, "hasAtherosclerosis") and (
            _b(data, "hadRevascularization")
            or pad_presentation == "clti"
            or pad_presentation == "claudication"
        )
        if not eligible:
            details = "Patient does not meet criteria for shared decision-making measure."
        elif pad_presentation == "ali":
            excluded = True
            exclusion_reason = "Emergency revascularization for acute limb ischemia — shared decision-making not feasible."
            details = exclusion_reason
        else:
            passed = _b(data, "multidisciplinaryDiscussionDocumented")
            details = (
                "Shared decision-making discussion documented. Measure PASSES."
                if passed
                else "Shared decision-making discussion not documented. Measure FAILS."
            )

    elif mid == "QM-8":
        # Post-Revascularization Surveillance
        eligible = _b(data, "hadRevascularization")
        if not eligible:
            details = "Patient has not undergone lower extremity revascularization."
        else:
            passed = _b(data, "abiDocumented")
            details = (
                "Post-revascularization ABI documented. Measure PASSES (duplex ultrasound should also be documented per full measure specification)."
                if passed
                else "Post-revascularization ABI not documented. Measure FAILS."
            )

    else:
        details = "Unknown measure ID."

    if not eligible:
        result = "not_applicable"
    elif excluded:
        result = "excluded"
    elif passed:
        result = "pass"
    else:
        result = "fail"

    return {
        "measure": measure,
        "result": result,
        "eligible": eligible,
        "passed": passed,
        "excluded": excluded,
        "exclusionReason": exclusion_reason,
        "details": details,
    }


def _summarize(group: list[dict]) -> dict:
    eligible = [s for s in group if s["eligible"]]
    passed = len([s for s in eligible if s["passed"] and not s["excluded"]])
    failed = len([s for s in eligible if not s["passed"] and not s["excluded"]])
    excluded = len([s for s in eligible if s["excluded"]])
    not_applicable = len([s for s in group if not s["eligible"]])
    denominator = passed + failed
    return {
        "total": len(group),
        "passed": passed,
        "failed": failed,
        "excluded": excluded,
        "notApplicable": not_applicable,
        "passRate": js_round((passed / denominator) * 100) if denominator > 0 else 0,
    }


_RECOMMENDATION_BY_ID = {
    "PM-1": "Order ABI testing and document results within 12 months.",
    "PM-2": "Prescribe high-intensity statin therapy (atorvastatin 40–80 mg or rosuvastatin 20–40 mg).",
    "PM-3": "Prescribe antithrombotic therapy: aspirin 81 mg daily, clopidogrel 75 mg daily, or rivaroxaban 2.5 mg BID + aspirin 100 mg daily (COMPASS regimen).",
    "PM-4": "Measure blood pressure and document management plan targeting SBP <130 mmHg.",
    "PM-5": "Prescribe ACE inhibitor (e.g., ramipril 10 mg daily) or ARB for cardiovascular risk reduction.",
    "PM-6": "Screen for tobacco use and offer cessation counseling + pharmacotherapy (varenicline preferred).",
    "PM-7": "Refer patient to Medicare-covered supervised exercise therapy (SET) program for claudication.",
    "QM-1": "Measure HbA1c and document diabetes management plan (target HbA1c <7% or individualized).",
    "QM-2": "Perform foot examination and provide preventive foot care education (self-inspection, footwear, wound prevention).",
    "QM-4": "Document race/ethnicity and screen for social determinants of health (food, housing, transportation, insurance).",
    "QM-5": "Perform preoperative duplex ultrasound saphenous vein mapping before bypass surgery.",
    "QM-6": "Convene multidisciplinary team discussion (vascular surgery/IR + wound care/podiatry) before definitive CLTI treatment.",
    "QM-7": "Document shared decision-making discussion including treatment options, risks/benefits, and patient preferences.",
    "QM-8": "Document post-revascularization ABI and duplex ultrasound surveillance within 30 days of procedure.",
}


def assess(data: dict) -> dict:
    data = _derive_numeric_flags(_derive_presentation_flags(dict(data)))
    scores = [score_pad_qm_measure(measure, data) for measure in PAD_QM_MEASURES]

    pms = [s for s in scores if s["measure"]["type"] == "performance"]
    qms = [s for s in scores if s["measure"]["type"] == "quality"]

    pm_summary = _summarize(pms)
    qm_summary = _summarize(qms)

    all_eligible = [s for s in scores if s["eligible"] and not s["excluded"]]
    overall_pass_rate = (
        js_round((len([s for s in all_eligible if s["passed"]]) / len(all_eligible)) * 100)
        if len(all_eligible) > 0
        else 0
    )

    # Stable sort: performance measures before quality measures.
    priority_gaps = [
        s for s in scores if s["eligible"] and not s["excluded"] and not s["passed"]
    ]
    priority_gaps.sort(key=lambda s: 0 if s["measure"]["type"] == "performance" else 1)

    recommendations: list[str] = []
    ldlc = data.get("ldlcValue")
    for gap in priority_gaps:
        gid = gap["measure"]["id"]
        if gid == "QM-3":
            ldlc_str = f"{ldlc} mg/dL" if ldlc is not None else "above goal"
            recommendations.append(
                f"LDL-C {ldlc_str} — consider PCSK9 inhibitor (evolocumab or alirocumab), "
                "ezetimibe, bempedoic acid, or inclisiran."
            )
        elif gid in _RECOMMENDATION_BY_ID:
            recommendations.append(_RECOMMENDATION_BY_ID[gid])

    return {
        "scores": scores,
        "performanceMeasuresSummary": pm_summary,
        "qualityMeasuresSummary": qm_summary,
        "overallPassRate": overall_pass_rate,
        "priorityGaps": priority_gaps,
        "recommendations": recommendations,
    }
