"""Pulmonary Embolism Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/peLogic.ts (evaluatePE).

This engine is self-contained: the TS ``evaluatePE`` does NOT depend on the
peClassification / ecmoCandidacy helpers (those back a different engine). All
category assignment, anticoagulation, advanced-therapy, ECMO, monitoring, and
disposition logic is reproduced here exactly.

Input keys equal the ``PEInput`` interface field names. Missing keys fall back
to ``defaultPEInput`` (mirroring the TS test harness, which spreads form data
over ``defaultPEInput``). Comparisons on the string-enum and boolean fields are
exact, matching the TS ``===`` semantics.
"""

from __future__ import annotations

from app.recommendations.jslib import includes, truthy

LOGIC_KEY = "pe"

# ─── Default Input (mirrors defaultPEInput in peLogic.ts) ────────────────────
_DEFAULTS: dict = {
    "presentation": "symptomatic_stable",
    "hemodynamicStatus": "stable",
    "peBurden": "lobar",
    "sPESI": 1,
    "hestiaScore": 0,
    "rvStatus": "normal",
    "troponinElevated": False,
    "bnpElevated": False,
    "lactateElevated": False,
    "lactateLevel": "normal",
    "ageOver75": False,
    "activeBleedingRisk": False,
    "recentSurgery": False,
    "priorICH": False,
    "isPregnant": False,
    "cancerActive": False,
    "priorPEorDVT": False,
    "unprovoked": True,
    "thrombophilia": False,
    "pertActivated": False,
    "echoAvailable": True,
    "ctpaPerformed": True,
    "rvLvRatio": 0.8,
    "considerECMO": False,
    "ecmoContraindications": [],
    "anticoagulationPreference": "doac_preferred",
    "creatinineClearance": 80,
}


def assess(data: dict) -> dict:
    input_ = dict(_DEFAULTS)
    input_.update(data or {})

    urgent_flags: list[str] = []
    references: list[str] = [
        "2026 AHA/ACC/ACCP/ACEP/CHEST/SCAI/SHM/SIR/SVM/SVN Guideline for the Evaluation and Management of Acute Pulmonary Embolism in Adults. Circulation. 2026;153:e977–e1051.",
        "ESC 2019 Guidelines on Acute Pulmonary Embolism",
        "STORM-PE Trial (2025) — Mechanical thrombectomy vs anticoagulation in intermediate-to-high risk PE. Circulation.",
        "HI-PEITHO Trial (2026) — Low-dose USAT alteplase vs anticoagulation in intermediate-high risk PE. EHJ Acute Cardiovascular Care.",
        "PEITHO-1 Trial (2014) — Tenecteplase vs anticoagulation in intermediate-high risk PE. NEJM.",
        "PEERLESS Trial (2024) — FlowTriever vs CDT in intermediate-high risk PE.",
        "ELSO Guidelines for VA-ECMO in Cardiopulmonary Failure (2024)",
        "RENOVE Trial (2023) — Half-dose vs full-dose DOAC for extended anticoagulation in VTE.",
        "API-CAT Trial (2024) — Apixaban 2.5mg BID vs 5mg BID for extended anticoagulation in cancer-associated VTE.",
    ]

    presentation = input_["presentation"]
    hemodynamic_status = input_["hemodynamicStatus"]
    pe_burden = input_["peBurden"]
    s_pesi = input_["sPESI"]
    hestia_score = input_["hestiaScore"]
    rv_status = input_["rvStatus"]
    lactate_level = input_["lactateLevel"]
    rv_lv_ratio = input_["rvLvRatio"]

    # ─── Step 1: Determine AHA/ACC 2026 Category ─────────────────────────────
    acc_aha_category = "B"
    acc_aha_category_description = ""
    esc_equivalent = ""
    esc_esc_equivalent_description = ""
    risk_level = "low"

    has_rv_dysfunction = rv_status == "dysfunction_imaging" or rv_status == "dysfunction_both"
    has_biomarker = truthy(input_["troponinElevated"]) or truthy(input_["bnpElevated"])
    has_both = has_rv_dysfunction and has_biomarker

    if presentation == "incidental_asymptomatic":
        acc_aha_category = "A"
        acc_aha_category_description = (
            "Category A: Incidental/subclinical PE — found on imaging performed for another indication, no PE-related symptoms."
        )
        esc_equivalent = "Low Risk"
        esc_esc_equivalent_description = (
            "ESC 2019: Low-risk PE (PESI I-II, sPESI 0, no RV dysfunction, no biomarker elevation)."
        )
        risk_level = "low"
    elif hemodynamic_status == "refractory_arrest":
        acc_aha_category = "E2"
        acc_aha_category_description = (
            "Category E2: Refractory cardiopulmonary failure — refractory shock or cardiac arrest requiring CPR."
        )
        esc_equivalent = "High Risk (Massive PE)"
        esc_esc_equivalent_description = (
            "ESC 2019: High-risk/massive PE — hemodynamic instability with cardiac arrest or refractory shock."
        )
        risk_level = "critical"
        urgent_flags.append(
            "CRITICAL: Category E2 — Refractory shock/cardiac arrest. Activate PERT immediately. Consider VA-ECMO as bridge to definitive therapy. Systemic thrombolysis reasonable if ECMO unavailable."
        )
    elif hemodynamic_status == "hypotensive_shock":
        acc_aha_category = "E1"
        acc_aha_category_description = (
            "Category E1: Cardiopulmonary failure — persistent hypotension (SBP <90 mmHg or >40 mmHg drop) with cardiogenic shock."
        )
        esc_equivalent = "High Risk (Massive PE)"
        esc_esc_equivalent_description = (
            "ESC 2019: High-risk/massive PE — hemodynamic instability with SBP <90 mmHg or vasopressor requirement."
        )
        risk_level = "high"
        urgent_flags.append(
            "URGENT: Category E1 — Hemodynamic instability. Activate PERT. Advanced therapy (systemic tPA, CDT, MT, or surgical embolectomy) is reasonable (Class 2a, 2026 AHA/ACC)."
        )
    elif hemodynamic_status == "shock_normotensive" and lactate_level == "elevated":
        acc_aha_category = "D2"
        acc_aha_category_description = (
            "Category D2: Incipient cardiopulmonary failure with end-organ dysfunction — normotensive but lactate >4 mmol/L, rising creatinine, or altered mentation."
        )
        esc_equivalent = "Intermediate-High Risk"
        esc_esc_equivalent_description = (
            "ESC 2019: Intermediate-high risk PE — RV dysfunction + elevated troponin, with signs of hemodynamic deterioration."
        )
        risk_level = "high"
        urgent_flags.append(
            "HIGH RISK: Category D2 — End-organ dysfunction despite normal BP. Lactate >4 mmol/L or rising creatinine. Advanced therapy may be considered (Class 2b). Urgent PERT activation (Class 1)."
        )
    elif hemodynamic_status == "shock_normotensive" or hemodynamic_status == "borderline":
        acc_aha_category = "D1"
        acc_aha_category_description = (
            "Category D1: Incipient cardiopulmonary failure — normotensive but signs of impending shock (borderline BP, HR >100, lactate 2-4 mmol/L, worsening hypoxia)."
        )
        esc_equivalent = "Intermediate-High Risk"
        esc_esc_equivalent_description = (
            "ESC 2019: Intermediate-high risk PE — RV dysfunction + elevated troponin, borderline hemodynamics."
        )
        risk_level = "intermediate_high"
        urgent_flags.append(
            "ELEVATED RISK: Category D1 — Borderline hemodynamics with signs of incipient failure. Serial lactate, troponin, and echo monitoring required. PERT activation recommended (Class 1)."
        )
    elif s_pesi >= 1 or hestia_score >= 1:
        # Elevated severity score — further stratify by RV/biomarker
        if has_both:
            acc_aha_category = "C3"
            acc_aha_category_description = (
                "Category C3: Elevated severity score + RV dysfunction on imaging AND elevated biomarkers (troponin/BNP) — intermediate-high risk."
            )
            esc_equivalent = "Intermediate-High Risk"
            esc_esc_equivalent_description = (
                "ESC 2019: Intermediate-high risk PE — sPESI ≥1 + RV dysfunction on imaging + elevated troponin. Monitoring in ICU/HDU recommended."
            )
            risk_level = "intermediate_high"
            urgent_flags.append(
                "INTERMEDIATE-HIGH RISK: Category C3 — RV dysfunction + elevated biomarkers. PEITHO-1 showed thrombolysis reduces decompensation but increases ICH. HI-PEITHO (2026): low-dose USAT reduced deterioration 10.3%→4% with no ICH. STORM-PE (2025): mechanical thrombectomy superior to anticoagulation alone. PERT activation Class 1."
            )
        elif has_rv_dysfunction or has_biomarker:
            acc_aha_category = "C2"
            acc_aha_category_description = (
                "Category C2: Elevated severity score + RV dysfunction OR elevated biomarkers (not both) — intermediate-low risk."
            )
            esc_equivalent = "Intermediate-Low Risk"
            esc_esc_equivalent_description = (
                "ESC 2019: Intermediate-low risk PE — sPESI ≥1 + RV dysfunction OR elevated troponin (not both). Inpatient monitoring recommended."
            )
            risk_level = "intermediate_low"
        else:
            acc_aha_category = "C1"
            acc_aha_category_description = (
                "Category C1: Elevated severity score but normal RV function and normal biomarkers — elevated clinical risk without imaging/biomarker confirmation."
            )
            esc_equivalent = "Intermediate-Low Risk"
            esc_esc_equivalent_description = (
                "ESC 2019: Intermediate-low risk PE — sPESI ≥1 but no RV dysfunction and no biomarker elevation."
            )
            risk_level = "intermediate_low"
    else:
        # sPESI 0, Hestia 0
        acc_aha_category = "B"
        acc_aha_category_description = (
            "Category B: Symptomatic PE with low severity — sPESI 0, Hestia 0, no RV dysfunction, no biomarker elevation. Early discharge is reasonable."
        )
        esc_equivalent = "Low Risk"
        esc_esc_equivalent_description = (
            "ESC 2019: Low-risk PE — PESI I-II or sPESI 0, no RV dysfunction, no biomarker elevation. Outpatient treatment or early discharge recommended."
        )
        risk_level = "low"

    # ─── Step 2: PERT Recommendation ─────────────────────────────────────────
    if includes(["C3", "D1", "D2", "E1", "E2"], acc_aha_category):
        pert_recommendation = (
            "Activate PERT (Pulmonary Embolism Response Team). Multidisciplinary team assessment including cardiology, pulmonology, hematology, and IR/cardiac surgery. Real-time decision-making for advanced therapy."
        )
        pert_class = "Class 1, Level B-NR (2026 AHA/ACC)"
    elif acc_aha_category == "C2":
        pert_recommendation = (
            "PERT activation is reasonable for Category C2 patients with clinical deterioration or high-risk features. Monitor closely for progression to C3 or D."
        )
        pert_class = "Class 2a, Level B-NR (2026 AHA/ACC)"
    else:
        pert_recommendation = (
            "PERT activation not routinely indicated for Category A, B, or C1. Standard anticoagulation management with outpatient follow-up."
        )
        pert_class = "Not indicated (Class 3: No Benefit for low-risk categories)"

    # ─── Step 3: Anticoagulation Strategy ────────────────────────────────────
    if truthy(input_["activeBleedingRisk"]) or truthy(input_["priorICH"]):
        urgent_flags.append(
            "BLEEDING RISK: Active bleeding or prior ICH. Anticoagulation contraindicated. Consider IVC filter as bridge. Reassess daily."
        )
        anticoagulation_strategy = (
            "Anticoagulation CONTRAINDICATED. IVC filter placement may be considered as a temporary bridge (Class 2b). Reassess bleeding risk daily and initiate anticoagulation as soon as safe."
        )
        anticoagulation_class = "IVC filter: Class 2b (2026 AHA/ACC). Routine IVC filter in anticoagulated patients: Class 3 Harm, Level A."
    elif includes(["E1", "E2"], acc_aha_category) or input_["anticoagulationPreference"] == "ufh_required":
        anticoagulation_strategy = (
            "Unfractionated heparin (UFH) IV bolus + infusion: 80 units/kg bolus, then 18 units/kg/hr. Titrate to aPTT 60-100s. UFH preferred when thrombolysis or surgical intervention is planned (rapid reversibility). Avoid LMWH if CrCl <30 mL/min."
        )
        anticoagulation_class = "Class 1, Level B-R (2026 AHA/ACC)"
    elif truthy(input_["isPregnant"]):
        anticoagulation_strategy = (
            "LMWH (enoxaparin 1 mg/kg BID) is preferred in pregnancy. DOACs are contraindicated (teratogenic, cross placenta). Continue LMWH throughout pregnancy and for ≥6 weeks postpartum (minimum 3 months total)."
        )
        anticoagulation_class = "Class 1, Level B-R (2026 AHA/ACC)"
        urgent_flags.append(
            "PREGNANCY: DOACs contraindicated. Use LMWH throughout pregnancy. Consult MFM and hematology."
        )
    elif truthy(input_["cancerActive"]):
        anticoagulation_strategy = (
            "DOAC (apixaban or rivaroxaban) preferred for cancer-associated VTE (CARAVAGGIO, SELECT-D trials). LMWH acceptable alternative. Avoid DOACs with GI malignancy (higher GI bleeding risk — consider LMWH). Duration: indefinite while cancer active."
        )
        anticoagulation_class = "Class 1, Level B-R (2026 AHA/ACC); API-CAT Trial (2024)"
    elif input_["creatinineClearance"] < 30:
        anticoagulation_strategy = (
            "Avoid rivaroxaban and edoxaban in severe renal impairment (CrCl <30 mL/min). Apixaban 10mg BID x7d then 5mg BID is preferred DOAC (least renal clearance). LMWH dose-reduce or use UFH if CrCl <15 mL/min."
        )
        anticoagulation_class = "Class 1, Level B-R (2026 AHA/ACC)"
    else:
        anticoagulation_strategy = (
            "DOAC preferred over VKA (Class 1, Level B-R). Options: Apixaban 10mg BID x7d then 5mg BID; Rivaroxaban 15mg BID x21d then 20mg QD; Edoxaban 60mg QD (after 5-10d LMWH); Dabigatran 150mg BID (after 5-10d LMWH). DOACs have comparable efficacy and lower ICH risk vs warfarin."
        )
        anticoagulation_class = "Class 1, Level B-R (2026 AHA/ACC)"

    # Extended anticoagulation
    if truthy(input_["unprovoked"]) and not truthy(input_["activeBleedingRisk"]):
        extended_anticoagulation = (
            "Extended anticoagulation (>3-6 months) recommended for unprovoked PE with low-moderate bleeding risk (Class 1). Half-dose apixaban 2.5mg BID or rivaroxaban 10mg QD are preferred over full-dose for extended therapy (RENOVE 2023, API-CAT 2024) — comparable efficacy, lower bleeding. Re-evaluate annually."
        )
    elif truthy(input_["cancerActive"]):
        extended_anticoagulation = (
            "Indefinite anticoagulation while cancer is active. Half-dose apixaban 2.5mg BID is an option after initial 6 months (API-CAT 2024). Reassess when cancer enters remission."
        )
    elif truthy(input_["thrombophilia"]):
        extended_anticoagulation = (
            "Extended anticoagulation recommended for high-risk thrombophilia (antiphospholipid syndrome, homozygous Factor V Leiden, combined defects). Warfarin preferred over DOAC for antiphospholipid syndrome (TRAPS trial)."
        )
    else:
        extended_anticoagulation = (
            "Standard duration: 3 months for provoked PE (reversible risk factor). Reassess after 3 months for extended therapy based on bleeding risk, patient preference, and recurrence risk."
        )

    # ─── Step 4: Advanced Therapy ────────────────────────────────────────────
    advanced_therapy_recommendation = ""
    advanced_therapy_class = ""
    preferred_advanced_therapy = ""
    trial_evidence: list[dict] = []

    if includes(["A", "B", "C1", "C2"], acc_aha_category):
        advanced_therapy_recommendation = (
            "Advanced therapy (systemic thrombolysis, CDT, mechanical thrombectomy) is NOT recommended for Categories A, B, C1, and C2. Risk of bleeding (including ICH) outweighs benefit in hemodynamically stable patients."
        )
        advanced_therapy_class = "Class 3: Harm (systemic thrombolysis in low/intermediate-low risk), Level A"
        preferred_advanced_therapy = "None — anticoagulation only"
    elif acc_aha_category == "C3":
        advanced_therapy_recommendation = (
            "Category C3 (intermediate-high risk): Role of advanced therapy is evolving. Anticoagulation alone is standard. Advanced therapy may be considered for patients with high-risk features (RV/LV >1.5, troponin significantly elevated, ≥2 signs of cardiorespiratory instability: SBP <110, HR >100, hypoxemia). HI-PEITHO (2026): low-dose USAT (18mg alteplase/6h) reduced cardiorespiratory deterioration from 10.3% to 4% with no ICH. STORM-PE (2025): mechanical thrombectomy (FlowTriever) superior to anticoagulation alone at 90-day functional outcomes. Systemic full-dose thrombolysis NOT recommended due to ICH risk (PEITHO-1: 2% ICH rate)."
        )
        advanced_therapy_class = "Class 2b (may be considered) for selected C3 patients; Class 3 Harm for routine use"
        preferred_advanced_therapy = (
            "If advanced therapy pursued: Mechanical thrombectomy (FlowTriever) preferred where available (STORM-PE 2025, PEERLESS 2024). Low-dose USAT (18mg alteplase/6h) is an alternative (HI-PEITHO 2026). Avoid full-dose systemic thrombolysis."
        )
        trial_evidence.extend([
            {
                "trial": "HI-PEITHO",
                "year": 2026,
                "finding": "Low-dose USAT alteplase (~18mg/6h) vs anticoagulation alone in intermediate-high risk PE: cardiorespiratory deterioration 4% vs 10.3% (p<0.05). No intracranial hemorrhages. Rescue therapy 2.9% vs 9.2%. 1-month poor functional status 6.5% vs 14.7% (p=0.002). Patients >75y and RV/LV 1-1.5 may not benefit.",
                "relevance": "Supports low-dose peripheral USAT as safe and effective for selected C3 patients. No evidence CDT is superior to peripheral administration of same dose.",
            },
            {
                "trial": "STORM-PE",
                "year": 2025,
                "finding": "Mechanical thrombectomy (Penumbra FlowTriever/CAVT) + anticoagulation vs anticoagulation alone in intermediate-to-high risk PE: significantly better RV/LV ratio improvement, lower clinical deterioration, greater 6-minute walk distance at 90 days. Comparable safety profile.",
                "relevance": "Supports mechanical thrombectomy as preferred advanced therapy for C3-D patients over anticoagulation alone, particularly where PERT and IR expertise available.",
            },
            {
                "trial": "PEITHO-1",
                "year": 2014,
                "finding": "Tenecteplase (full-dose) vs anticoagulation in intermediate-high risk PE: reduced hemodynamic collapse (1.6% vs 5%) but increased ICH (2% vs 0.2%) and major bleeding (6.3% vs 1.2%). No mortality benefit at 7 days or 30 days.",
                "relevance": "Established that full-dose systemic thrombolysis in intermediate-high risk PE reduces decompensation but at unacceptable ICH risk. Supports move toward lower-dose/catheter-directed approaches.",
            },
        ])
    elif includes(["D1", "D2"], acc_aha_category):
        advanced_therapy_recommendation = (
            "Category D (incipient failure): Advanced therapy may be considered (Class 2b). Mechanical thrombectomy (FlowTriever) or CDT preferred over full-dose systemic thrombolysis given comparable efficacy and lower bleeding risk. Systemic thrombolysis reserved for patients without access to catheter-based therapy or as bridge to ECMO."
        )
        advanced_therapy_class = "Class 2b (2026 AHA/ACC)"
        preferred_advanced_therapy = (
            "Mechanical thrombectomy (FlowTriever) or USAT CDT preferred. Full-dose systemic thrombolysis (alteplase 100mg/2h or tenecteplase weight-based) as fallback."
        )
        trial_evidence.extend([
            {
                "trial": "STORM-PE",
                "year": 2025,
                "finding": "Mechanical thrombectomy superior to anticoagulation alone in intermediate-to-high risk PE at 90-day functional outcomes.",
                "relevance": "Supports MT as preferred advanced therapy in D1-D2 patients.",
            },
            {
                "trial": "PEERLESS",
                "year": 2024,
                "finding": "FlowTriever mechanical thrombectomy vs catheter-directed thrombolysis (CDT) in intermediate-high risk PE: FlowTriever achieved superior clinical success, lower major bleeding, shorter ICU stay.",
                "relevance": "Supports mechanical thrombectomy over CDT as first-line advanced therapy where available.",
            },
        ])
    elif acc_aha_category == "E1":
        advanced_therapy_recommendation = (
            "Category E1 (overt cardiopulmonary failure): Advanced therapy is reasonable (Class 2a). Systemic thrombolysis (alteplase 100mg/2h or tenecteplase weight-based) is the fastest option. Surgical embolectomy is reasonable if thrombolysis contraindicated or fails. Catheter-based therapy (MT or CDT) is an alternative. VA-ECMO as bridge to definitive therapy if failing vasopressors."
        )
        advanced_therapy_class = "Class 2a (2026 AHA/ACC)"
        preferred_advanced_therapy = (
            "Systemic thrombolysis (alteplase 100mg/2h) for immediate hemodynamic stabilization. Mechanical thrombectomy or surgical embolectomy for thrombolysis failure or contraindication. VA-ECMO for refractory shock."
        )
        urgent_flags.append(
            "AVOID deep sedation/intubation unless absolutely necessary — cardiac arrest rate 19-28% after induction in PE with RV failure (Class 3: Harm, 2026 AHA/ACC)."
        )
        trial_evidence.append(
            {
                "trial": "STORM-PE",
                "year": 2025,
                "finding": "Mechanical thrombectomy + anticoagulation vs anticoagulation alone: superior outcomes in intermediate-to-high risk PE.",
                "relevance": "Supports MT as advanced therapy option in E1 patients.",
            }
        )
    elif acc_aha_category == "E2":
        advanced_therapy_recommendation = (
            "Category E2 (refractory shock/cardiac arrest): Systemic thrombolysis is reasonable (Class 2a). VA-ECMO as bridge to definitive therapy (surgical embolectomy or MT) is preferred over surgical embolectomy alone in cardiac arrest (Class 2a). Surgical embolectomy NOT recommended over VA-ECMO in cardiac arrest (Class 3: Harm). CPR should continue during thrombolysis administration (continue CPR for ≥60-90 min after tPA)."
        )
        advanced_therapy_class = "Class 2a (systemic thrombolysis, VA-ECMO); Class 3 Harm (surgical embolectomy over VA-ECMO in arrest)"
        preferred_advanced_therapy = (
            "VA-ECMO (if available) as bridge to MT or surgical embolectomy. Systemic thrombolysis (alteplase 50mg rapid bolus in arrest) if ECMO unavailable. Continue CPR ≥60-90 min post-tPA."
        )
        urgent_flags.append(
            "CARDIAC ARREST / REFRACTORY SHOCK: Activate ECMO team immediately if available. Systemic thrombolysis (alteplase 50mg bolus) if ECMO not available. Continue CPR ≥60-90 min after tPA. Surgical embolectomy NOT preferred over VA-ECMO in arrest."
        )

    # ─── Step 5: ECMO Assessment ─────────────────────────────────────────────
    ecmo_assessment = None

    if truthy(input_["considerECMO"]) or includes(["E1", "E2"], acc_aha_category):
        absolute_contraindications: list[str] = []
        relative_contraindications: list[str] = []

        for c in input_["ecmoContraindications"]:
            if c == "severe_ar":
                absolute_contraindications.append(
                    "Severe aortic regurgitation (without IABP support) — VA-ECMO will increase afterload and worsen AR"
                )
            elif c == "aortic_dissection":
                absolute_contraindications.append(
                    "Aortic dissection — VA-ECMO cannulation contraindicated"
                )
            elif c == "unwitnessed_arrest_30min":
                absolute_contraindications.append(
                    "Unwitnessed cardiac arrest >30 minutes without CPR — irreversible anoxic brain injury likely"
                )
            elif c == "severe_brain_injury":
                absolute_contraindications.append(
                    "Severe irreversible brain injury — ECMO would not result in meaningful neurological recovery"
                )
            elif c == "terminal_illness":
                absolute_contraindications.append(
                    "Terminal illness with no meaningful recovery expected — ECMO is not appropriate"
                )
            elif c == "uncontrolled_bleeding":
                relative_contraindications.append(
                    "Uncontrolled bleeding — UFH anticoagulation required on ECMO increases bleeding risk significantly"
                )
            elif c == "age_over_75":
                relative_contraindications.append(
                    "Age >75 — center-dependent; higher mortality on ECMO but not absolute contraindication"
                )
            elif c == "bmi_over_40":
                relative_contraindications.append(
                    "BMI >40 — femoral access challenges; consider axillary cannulation"
                )
            elif c == "active_malignancy_poor_prognosis":
                relative_contraindications.append(
                    "Active malignancy with poor prognosis — goals of care discussion required before ECMO"
                )
            elif c == "severe_pad":
                relative_contraindications.append(
                    "Severe peripheral arterial disease — femoral access may be compromised; consider alternative cannulation sites"
                )
            elif c == "prior_cardiac_surgery":
                relative_contraindications.append(
                    "Prior cardiac surgery with dense adhesions — surgical ECMO access may be difficult"
                )

        has_absolute_contraindication = len(absolute_contraindications) > 0
        has_relative_contraindication = len(relative_contraindications) > 0

        if has_absolute_contraindication:
            candidacy = "absolute_contraindication"
            ecmo_recommendation = (
                "VA-ECMO is CONTRAINDICATED due to absolute contraindication(s). Proceed with systemic thrombolysis or surgical embolectomy if feasible. Goals-of-care discussion required."
            )
        elif has_relative_contraindication:
            candidacy = "relative_contraindication"
            ecmo_recommendation = (
                "VA-ECMO has relative contraindication(s). Multidisciplinary team (PERT + ECMO team) should weigh risks and benefits. ECMO may still be appropriate if benefits outweigh risks."
            )
        elif not includes(["E1", "E2", "D2"], acc_aha_category):
            candidacy = "not_indicated"
            ecmo_recommendation = (
                "VA-ECMO is not indicated for this risk category. ECMO is reserved for Category E1-E2 (overt/refractory cardiopulmonary failure) or D2 with rapid deterioration."
            )
        else:
            candidacy = "candidate"
            ecmo_recommendation = (
                "Patient appears to be an ECMO candidate. Activate ECMO team immediately. VA-ECMO preferred over VV-ECMO in PE (primary problem is RV failure, not gas exchange). Use as bridge to: mechanical thrombectomy, surgical embolectomy, or spontaneous recovery."
            )

        ecmo_assessment = {
            "candidacy": candidacy,
            "absoluteContraindications": absolute_contraindications,
            "relativeContraindications": relative_contraindications,
            "ecmoType": "VA-ECMO (venoarterial) — preferred in PE due to RV failure as primary mechanism. VV-ECMO does not unload the RV.",
            "bridgeTo": "Bridge to: (1) Mechanical thrombectomy (FlowTriever), (2) Surgical embolectomy, (3) Catheter-directed thrombolysis, or (4) Spontaneous RV recovery with anticoagulation.",
            "anticoagulationOnECMO": "UFH preferred on ECMO. Target ACT 160-200s (or anti-Xa 0.3-0.5 IU/mL). Avoid systemic thrombolysis while on ECMO if possible (high bleeding risk). If thrombolysis required, accept higher bleeding risk and monitor closely.",
            "decannulationCriteria": "RV recovery on serial echo (RV/LV <1, TAPSE >15mm), hemodynamic stability off vasopressors for ≥4 hours, lactate normalizing, adequate cardiac output on reduced ECMO flow.",
            "recommendation": ecmo_recommendation,
        }

        if candidacy == "candidate":
            urgent_flags.append(
                "ECMO CANDIDATE: Activate ECMO team. VA-ECMO as bridge to definitive therapy (MT, surgical embolectomy, or recovery). UFH anticoagulation on ECMO (ACT 160-200s). ELSO 2024 Guidelines."
            )

    # ─── Step 6: Monitoring Plan ─────────────────────────────────────────────
    if includes(["E1", "E2"], acc_aha_category):
        monitoring_plan = (
            "ICU admission. Continuous hemodynamic monitoring (arterial line, CVP). Serial troponin, BNP, lactate q4-6h. Echo within 1-2h of presentation and after any intervention. Vasopressor support (norepinephrine first-line for PE shock). Avoid intubation unless absolutely necessary (cardiac arrest risk 19-28% post-induction)."
        )
    elif includes(["D1", "D2", "C3"], acc_aha_category):
        monitoring_plan = (
            "ICU or step-down unit admission. Continuous telemetry and pulse oximetry. Serial troponin, BNP, lactate q6-8h. Echo within 12-24h. Repeat CTPA if clinical deterioration. PERT team involvement. Reassess for advanced therapy if hemodynamic deterioration."
        )
    elif includes(["C1", "C2"], acc_aha_category):
        monitoring_plan = (
            "Inpatient admission. Telemetry monitoring. Serial troponin and BNP at 6-12h. Echo if not already performed. Reassess Hestia/sPESI criteria at 24-48h for potential early discharge. Ambulation as tolerated."
        )
    else:
        monitoring_plan = (
            "Outpatient management or early discharge (Hestia/sPESI criteria met). Follow-up within 5-7 days. Anticoagulation education. Return precautions: worsening dyspnea, syncope, hemoptysis, new leg swelling."
        )

    # ─── Step 7: Disposition ─────────────────────────────────────────────────
    if includes(["E1", "E2"], acc_aha_category):
        disposition_recommendation = (
            "ICU admission. Immediate PERT activation. Advanced therapy decision within 1-2 hours."
        )
    elif includes(["D1", "D2"], acc_aha_category):
        disposition_recommendation = (
            "ICU or monitored step-down unit. PERT activation. Serial reassessment q4-6h."
        )
    elif acc_aha_category == "C3":
        disposition_recommendation = (
            "ICU or HDU admission. PERT activation. Echo and serial biomarkers. Advanced therapy discussion."
        )
    elif includes(["C1", "C2"], acc_aha_category):
        disposition_recommendation = (
            "Inpatient admission. Telemetry. Reassess for early discharge at 24-48h."
        )
    elif acc_aha_category == "B":
        disposition_recommendation = (
            "Early discharge is reasonable if Hestia criteria met (Class 2a). Outpatient DOAC. Follow-up in 5-7 days. Ensure adequate social support and patient education."
        )
    else:
        disposition_recommendation = (
            "Outpatient management. DOAC initiation. Follow-up within 5-7 days. Consider thrombophilia workup if unprovoked."
        )

    # ─── Step 8: Additional Urgent Flags ─────────────────────────────────────
    if truthy(input_["isPregnant"]):
        urgent_flags.append(
            "PREGNANCY: Consult MFM and hematology. LMWH only — DOACs contraindicated. Radiation exposure from CTPA must be weighed against V/Q scan. Delivery planning required."
        )

    if pe_burden == "subsegmental" and s_pesi == 0:
        urgent_flags.append(
            "SUBSEGMENTAL PE: Consider withholding anticoagulation in low-risk patients with subsegmental PE and no proximal DVT (Class 2b, 2026 AHA/ACC). Bilateral leg ultrasound recommended. Shared decision-making."
        )

    if rv_lv_ratio >= 1.5:
        urgent_flags.append(
            "RV/LV RATIO ≥1.5: Severe RV dilation — significantly elevated risk of hemodynamic decompensation. Escalate monitoring and consider PERT activation even if currently hemodynamically stable."
        )

    # ─── Primary Recommendation ───────────────────────────────────────────────
    if acc_aha_category == "A":
        primary_recommendation = (
            "Incidental PE: Anticoagulation is recommended for most patients (Class 1) unless high bleeding risk. Duration 3-6 months. Treat as symptomatic PE in terms of anticoagulation duration. No advanced therapy indicated."
        )
    elif acc_aha_category == "B":
        primary_recommendation = (
            "Low-risk PE: Early discharge with outpatient DOAC is reasonable if Hestia criteria met (Class 2a, 2026 AHA/ACC). Apixaban or rivaroxaban preferred. No advanced therapy. Follow-up in 5-7 days."
        )
    elif acc_aha_category == "C1":
        primary_recommendation = (
            "Intermediate-low risk (C1): Inpatient anticoagulation. Monitor for clinical deterioration. No advanced therapy indicated. Reassess at 24-48h for early discharge eligibility."
        )
    elif acc_aha_category == "C2":
        primary_recommendation = (
            "Intermediate-low risk (C2): Inpatient anticoagulation with close monitoring. Echo and serial biomarkers. PERT if deterioration. No advanced therapy unless progression to C3 or D."
        )
    elif acc_aha_category == "C3":
        primary_recommendation = (
            "Intermediate-high risk (C3): Anticoagulation + PERT activation (Class 1). Advanced therapy (low-dose USAT or mechanical thrombectomy) may be considered for high-risk C3 patients with ≥2 signs of instability (HI-PEITHO 2026, STORM-PE 2025). Avoid full-dose systemic thrombolysis (ICH risk). ICU/HDU monitoring."
        )
    elif acc_aha_category == "D1":
        primary_recommendation = (
            "Incipient failure (D1): PERT activation (Class 1). UFH anticoagulation. Advanced therapy (MT or CDT) may be considered (Class 2b). Serial lactate, echo, and hemodynamic monitoring. Prepare for escalation."
        )
    elif acc_aha_category == "D2":
        primary_recommendation = (
            "Incipient failure with end-organ dysfunction (D2): PERT activation (Class 1). UFH anticoagulation. Advanced therapy strongly considered (Class 2b). Assess ECMO candidacy. ICU admission."
        )
    elif acc_aha_category == "E1":
        primary_recommendation = (
            "Overt cardiopulmonary failure (E1): PERT activation (Class 1). UFH anticoagulation. Advanced therapy is reasonable (Class 2a): systemic thrombolysis (alteplase 100mg/2h), mechanical thrombectomy, or surgical embolectomy. VA-ECMO if failing vasopressors. Avoid intubation unless necessary."
        )
    else:
        primary_recommendation = (
            "Refractory shock/cardiac arrest (E2): Systemic thrombolysis (alteplase 50mg bolus in arrest) or VA-ECMO as bridge to MT/surgical embolectomy (Class 2a). Continue CPR ≥60-90 min post-tPA. Surgical embolectomy NOT preferred over VA-ECMO in arrest (Class 3: Harm). Activate ECMO team immediately."
        )

    return {
        "accAhaCategory": acc_aha_category,
        "accAhaCategoryDescription": acc_aha_category_description,
        "escEquivalent": esc_equivalent,
        "escEscEquivalentDescription": esc_esc_equivalent_description,
        "riskLevel": risk_level,
        "primaryRecommendation": primary_recommendation,
        "pertRecommendation": pert_recommendation,
        "pertClass": pert_class,
        "anticoagulationStrategy": anticoagulation_strategy,
        "anticoagulationClass": anticoagulation_class,
        "extendedAnticoagulation": extended_anticoagulation,
        "advancedTherapyRecommendation": advanced_therapy_recommendation,
        "advancedTherapyClass": advanced_therapy_class,
        "preferredAdvancedTherapy": preferred_advanced_therapy,
        "trialEvidence": trial_evidence,
        "ecmoAssessment": ecmo_assessment,
        "monitoringPlan": monitoring_plan,
        "dispositionRecommendation": disposition_recommendation,
        "urgentFlags": urgent_flags,
        "references": references,
    }
