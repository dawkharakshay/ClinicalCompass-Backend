"""Acute Ischemic Stroke clinical recommendation engine.

Ported 1:1 from old_static_code/client/src/lib/strokeLogic.ts (assessStroke).

Based on: AHA/ASA 2026 Guideline for Early Management of Acute Ischemic Stroke
Reference: Stroke. 2026; Prabhakaran S, et al.
Key trials: DAWN (PMID:29129157), DEFUSE-3 (PMID:29364767), NINDS tPA (PMID:7477192)

Disclaimer: For clinical decision support only. Does not replace clinical judgment.
"""

from __future__ import annotations

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "stroke"

_REFERENCES = [
    {
        "citation": (
            "Prabhakaran S, et al. 2026 Guideline for the Early Management of "
            "Patients with Acute Ischemic Stroke. Stroke. 2026."
        ),
        "pmid": "AHA/ASA 2026",
    },
    {
        "citation": (
            "Nogueira RG, et al. Thrombectomy 6 to 24 Hours after Stroke with a "
            "Mismatch between Deficit and Infarct (DAWN). N Engl J Med. "
            "2018;378(1):11-21."
        ),
        "pmid": "29129157",
    },
    {
        "citation": (
            "Albers GW, et al. Thrombectomy for Stroke at 6 to 16 Hours with "
            "Selection by Perfusion Imaging (DEFUSE-3). N Engl J Med. "
            "2018;378(8):708-718."
        ),
        "pmid": "29364767",
    },
    {
        "citation": (
            "The NINDS rt-PA Stroke Study Group. Tissue plasminogen activator for "
            "acute ischemic stroke. N Engl J Med. 1995;333(24):1581-1587."
        ),
        "pmid": "7477192",
    },
    {
        "citation": (
            "Zi W, et al. Effect of Endovascular Treatment Alone vs Intravenous "
            "Alteplase Plus Endovascular Treatment on Functional Outcome in "
            "Patients With Acute Ischemic Stroke (DEVT). JAMA. 2021;325(3):234-243."
        ),
        "pmid": "33464336",
    },
]


def assess(data: dict) -> dict:
    # ─── Inputs ──────────────────────────────────────────────────────────────
    onset_window = data.get("onsetWindow")
    nihss_score = parse_float(data.get("nihssScore"))
    is_disabling = truthy(data.get("isDisabling"))
    vessel_occlusion = data.get("vesselOcclusion")
    aspects_score = parse_float(data.get("aspectsScore"))
    imaging_availability = data.get("imagingAvailability")
    perfusion_mismatch_ratio = parse_float(data.get("perfusionMismatchRatio"))
    core_infarct_volume_ml = parse_float(data.get("coreInfarctVolumeMl"))
    age_years = parse_float(data.get("ageYears"))
    has_anticoagulation = truthy(data.get("hasAnticoagulation"))
    anticoagulant_type = data.get("anticoagulantType")
    inr_if_warfarin = parse_float(data.get("inrIfWarfarin"))
    platelet_count = parse_float(data.get("plateletCount"))
    blood_glucose = parse_float(data.get("bloodGlucose"))
    systolic_bp = parse_float(data.get("systolicBP"))
    has_history_ich = truthy(data.get("hasHistoryICH"))
    has_active_bleeding = truthy(data.get("hasActiveBleeding"))
    has_endocarditis = truthy(data.get("hasEndocarditis"))
    is_pregnant = truthy(data.get("isPregnant"))
    has_recent_intracranial_surgery = truthy(data.get("hasRecentIntracranialSurgery"))
    is_post_acute_phase = truthy(data.get("isPostAcutePhase"))
    stroke_mechanism = data.get("strokeMechanism")
    has_atrial_fibrillation = truthy(data.get("hasAtrialFibrillation"))
    nihss_at_presentation = parse_float(data.get("nihssAtPresentation"))

    urgent_flags: list[str] = []
    next_steps: list[str] = []
    monitoring_plan: list[str] = []

    # ─── Urgent Flags ───────────────────────────────────────────────────────
    if systolic_bp > 185:
        urgent_flags.append(
            f"SBP {_n(systolic_bp)} mmHg — must lower to ≤185/110 mmHg before IV thrombolysis"
        )
    if blood_glucose < 50 or blood_glucose > 400:
        urgent_flags.append(
            f"Blood glucose {_n(blood_glucose)} mg/dL — correct hypoglycemia/severe "
            "hyperglycemia before thrombolysis"
        )
    if has_active_bleeding:
        urgent_flags.append(
            "Active bleeding — IV thrombolysis and thrombectomy contraindicated"
        )
    if vessel_occlusion == "lvo_posterior" and nihss_score >= 10:
        urgent_flags.append(
            "Basilar artery occlusion with NIHSS ≥10 — high mortality without "
            "reperfusion; expedite thrombectomy evaluation"
        )
    if platelet_count < 100:
        urgent_flags.append(
            f"Platelet count {_n(platelet_count)}×10³/µL — thrombolysis contraindicated if <100"
        )

    # ─── IV Thrombolysis Eligibility ────────────────────────────────────────
    iv_thrombolysis_eligibility = "ineligible"
    iv_thrombolysis_rationale = ""

    absolute_contraindications = (
        has_active_bleeding
        or has_history_ich
        or has_endocarditis
        or is_pregnant
        or has_recent_intracranial_surgery
        or platelet_count < 100
        or (has_anticoagulation and anticoagulant_type == "warfarin" and inr_if_warfarin > 1.7)
        or (has_anticoagulation and anticoagulant_type == "doac")
    )

    if absolute_contraindications:
        iv_thrombolysis_eligibility = "ineligible"
        iv_thrombolysis_rationale = "Absolute contraindication to IV thrombolysis present."
        if has_history_ich:
            iv_thrombolysis_rationale += " Prior ICH."
        if has_active_bleeding:
            iv_thrombolysis_rationale += " Active bleeding."
        if anticoagulant_type == "doac":
            iv_thrombolysis_rationale += " Recent DOAC use."
        if platelet_count < 100:
            iv_thrombolysis_rationale += f" Platelet count {_n(platelet_count)}."
    elif (
        (onset_window == "within_3h" or onset_window == "3_to_4_5h")
        and is_disabling
        and nihss_score >= 1
    ):
        iv_thrombolysis_eligibility = "eligible"
        iv_thrombolysis_rationale = (
            "IV alteplase 0.9 mg/kg (max 90 mg) or tenecteplase 0.25 mg/kg "
            "(max 25 mg) within 3h — Class I recommendation (AHA/ASA 2026). "
            "Tenecteplase preferred if LVO present for logistical ease."
            if onset_window == "within_3h"
            else (
                "IV thrombolysis within 4.5h — Class I for most patients. Exclude: "
                "age >80 with severe stroke + diabetes, prior stroke + diabetes, "
                "NIHSS >25, anticoagulation, large infarct on imaging."
            )
        )
    elif (
        (onset_window == "4_5_to_9h" or onset_window == "wake_up_unknown")
        and (imaging_availability == "ct_perfusion" or imaging_availability == "mri_dwi")
        and perfusion_mismatch_ratio >= 1.8
        and core_infarct_volume_ml < 70
    ):
        iv_thrombolysis_eligibility = "eligible"
        iv_thrombolysis_rationale = (
            "Extended window thrombolysis (4.5-9h or wake-up stroke) — eligible "
            "based on perfusion imaging mismatch (EXTEND trial criteria: mismatch "
            "ratio ≥1.8, core <70 mL). AHA/ASA 2026 Class IIa."
        )
    elif onset_window == "within_3h" and not is_disabling:
        iv_thrombolysis_eligibility = "consider_with_caution"
        iv_thrombolysis_rationale = (
            "Non-disabling symptoms within 3h — shared decision-making. "
            "Thrombolysis may be considered but benefit uncertain for minor "
            "strokes (NIHSS 0-5 without disabling features)."
        )
    else:
        iv_thrombolysis_eligibility = "ineligible"
        iv_thrombolysis_rationale = (
            "Outside thrombolysis window or insufficient perfusion imaging "
            "evidence for extended window therapy."
        )

    # ─── Thrombectomy Eligibility ───────────────────────────────────────────
    thrombectomy_eligibility = "ineligible"
    thrombectomy_rationale = ""

    if vessel_occlusion == "lvo_anterior":
        if (
            (onset_window == "within_3h" or onset_window == "3_to_4_5h")
            and nihss_score >= 6
            and aspects_score >= 6
        ):
            thrombectomy_eligibility = "eligible"
            thrombectomy_rationale = (
                "LVO anterior circulation with NIHSS ≥6 and ASPECTS ≥6 within 6h "
                "— Class I thrombectomy indication (AHA/ASA 2026). Proceed immediately."
            )
        elif (
            (
                onset_window == "4_5_to_9h"
                or onset_window == "9_to_24h"
                or onset_window == "wake_up_unknown"
            )
            and nihss_score >= 6
            and age_years < 80
            and aspects_score >= 3
        ):
            thrombectomy_eligibility = "consider_extended_window"
            thrombectomy_rationale = (
                "Extended window thrombectomy (6-24h) — eligible if DAWN criteria "
                "(age/NIHSS/infarct volume mismatch) or DEFUSE-3 criteria "
                "(perfusion mismatch ratio ≥1.8, core <70 mL) met. AHA/ASA 2026 "
                "Class I for 6-16h, Class IIa for 16-24h."
            )
        elif aspects_score >= 3 and aspects_score <= 5 and nihss_score >= 6:
            thrombectomy_eligibility = "consider_extended_window"
            thrombectomy_rationale = (
                "Low ASPECTS (3-5) — thrombectomy may still be considered if age "
                "<80, NIHSS ≥6, and no significant mass effect (AHA/ASA 2026 Class "
                "IIb). Discuss with neurointerventional team."
            )
        else:
            thrombectomy_eligibility = "ineligible"
            thrombectomy_rationale = (
                "Does not meet standard thrombectomy criteria — NIHSS <6, ASPECTS "
                "<3, or outside window without perfusion mismatch."
            )
    elif vessel_occlusion == "lvo_posterior":
        if nihss_score >= 10 and onset_window != "beyond_24h":
            thrombectomy_eligibility = "eligible"
            thrombectomy_rationale = (
                "Basilar artery occlusion with NIHSS ≥10 and onset <24h — "
                "thrombectomy recommended (AHA/ASA 2026 Class I based on BASICS and "
                "ATTENTION trials). High mortality without reperfusion."
            )
        else:
            thrombectomy_eligibility = "consider_extended_window"
            thrombectomy_rationale = (
                "Basilar artery occlusion with NIHSS <10 — consider thrombectomy "
                "based on clinical trajectory and imaging. Discuss with "
                "neurointerventional team."
            )
    else:
        thrombectomy_eligibility = "ineligible"
        thrombectomy_rationale = (
            "Small vessel / lacunar stroke — thrombectomy not indicated. IV "
            "thrombolysis if eligible."
            if vessel_occlusion == "small_vessel"
            else (
                "No confirmed LVO — thrombectomy not indicated without vessel "
                "imaging confirmation."
            )
        )

    # ─── Anticoagulation Timing ─────────────────────────────────────────────
    anticoagulation_timing = ""
    if is_post_acute_phase and has_atrial_fibrillation:
        if nihss_at_presentation <= 8:
            anticoagulation_timing = (
                "Cardioembolic stroke (AF) with mild deficit (NIHSS ≤8) — initiate "
                "anticoagulation at 48-72h after onset if no hemorrhagic "
                "transformation on repeat imaging (AHA/ASA 2026 Class IIa)."
            )
        elif nihss_at_presentation <= 15:
            anticoagulation_timing = (
                "Moderate stroke (NIHSS 9-15) with AF — initiate anticoagulation at "
                "5-7 days if no hemorrhagic transformation. Repeat CT/MRI before "
                "starting."
            )
        else:
            anticoagulation_timing = (
                "Severe stroke (NIHSS >15) with AF — delay anticoagulation 14 days. "
                "High risk of hemorrhagic transformation. Aspirin in interim."
            )
    elif is_post_acute_phase and stroke_mechanism == "large_artery":
        anticoagulation_timing = (
            "Large artery atherosclerosis — dual antiplatelet therapy (aspirin + "
            "clopidogrel) for 21 days, then single antiplatelet. Anticoagulation "
            "not indicated unless AF identified."
        )
    elif is_post_acute_phase and stroke_mechanism == "small_vessel":
        anticoagulation_timing = (
            "Small vessel / lacunar stroke — single antiplatelet therapy (aspirin "
            "or clopidogrel). Anticoagulation not indicated."
        )
    else:
        anticoagulation_timing = (
            "Anticoagulation timing depends on stroke mechanism, severity, and "
            "hemorrhagic transformation risk. Reassess at 24-48h with repeat imaging."
        )

    # ─── Treatment Pathway ──────────────────────────────────────────────────
    if iv_thrombolysis_eligibility == "eligible" and thrombectomy_eligibility == "eligible":
        treatment_pathway = (
            "DUAL REPERFUSION: Administer IV thrombolysis immediately, then proceed "
            "directly to thrombectomy (bridging therapy). Do not delay thrombectomy "
            "for thrombolysis response."
        )
    elif iv_thrombolysis_eligibility == "eligible":
        treatment_pathway = (
            "IV THROMBOLYSIS: Administer tenecteplase 0.25 mg/kg (preferred) or "
            "alteplase 0.9 mg/kg. Admit to stroke unit. Monitor BP, neuro exam "
            "q15min × 2h, then q30min × 6h."
        )
    elif (
        thrombectomy_eligibility == "eligible"
        or thrombectomy_eligibility == "consider_extended_window"
    ):
        treatment_pathway = (
            "MECHANICAL THROMBECTOMY: Activate neurointerventional team immediately. "
            "Target door-to-puncture <60 min. Stent retriever or aspiration catheter "
            "per operator preference."
        )
    else:
        treatment_pathway = (
            "MEDICAL MANAGEMENT: Aspirin 325 mg loading dose (if no thrombolysis). "
            "Admit to stroke unit. BP management, glycemic control, dysphagia "
            "screening, early mobilization."
        )

    # ─── Next Steps ─────────────────────────────────────────────────────────
    next_steps.append(
        "Activate stroke code — time is brain (1.9 million neurons lost per minute "
        "without reperfusion)"
    )
    next_steps.append("Obtain STAT CT head (non-contrast) + CT angiography head/neck")
    if (
        (onset_window == "4_5_to_9h" or onset_window == "wake_up_unknown")
        and iv_thrombolysis_eligibility != "ineligible"
    ):
        next_steps.append(
            "CT perfusion or MRI DWI/PWI required for extended window eligibility "
            "assessment"
        )
    next_steps.append(
        "Continuous cardiac monitoring for 24-48h — detect AF (paroxysmal AF in "
        "10-15% of cryptogenic stroke)"
    )
    next_steps.append("Dysphagia screening before oral intake")
    next_steps.append("Early neurology consultation and stroke unit admission")

    # ─── Monitoring Plan ────────────────────────────────────────────────────
    monitoring_plan.append("Neurological exam q1h × 24h post-thrombolysis; q4h thereafter")
    monitoring_plan.append(
        "BP target: <180/105 mmHg for 24h post-thrombolysis; <140/90 mmHg after 24h"
    )
    monitoring_plan.append("Glucose target: 140-180 mg/dL (avoid hypoglycemia <80 mg/dL)")
    monitoring_plan.append("Repeat CT/MRI at 24-36h to assess hemorrhagic transformation")
    monitoring_plan.append(
        "Cardiac monitoring × 72h minimum; extended monitoring (30-day) for "
        "cryptogenic stroke"
    )

    evidence_level = (
        "Class I (AHA/ASA 2026) for IV thrombolysis within 4.5h and thrombectomy for "
        "LVO within 6h; Class I for basilar thrombectomy (BASICS, ATTENTION trials)"
    )

    rationale = (
        "The AHA/ASA 2026 guideline expands reperfusion windows based on perfusion "
        "imaging (DAWN, DEFUSE-3 for anterior circulation; BASICS, ATTENTION for "
        "posterior circulation). "
        "Tenecteplase is now preferred over alteplase for LVO due to logistical "
        "advantages. "
        "Anticoagulation timing in AF-related stroke follows a severity-based "
        "approach (48h for mild, 5-7d for moderate, 14d for severe)."
    )

    if thrombectomy_eligibility == "eligible":
        primary_recommendation = (
            "Mechanical Thrombectomy — activate neurointerventional team immediately"
        )
    elif iv_thrombolysis_eligibility == "eligible":
        primary_recommendation = (
            "IV Thrombolysis — administer tenecteplase/alteplase immediately"
        )
    else:
        primary_recommendation = (
            "Medical Management — stroke unit admission, antiplatelet therapy, risk "
            "factor control"
        )

    return {
        "primaryRecommendation": primary_recommendation,
        "ivThrombolysisEligibility": iv_thrombolysis_eligibility,
        "thrombectomyEligibility": thrombectomy_eligibility,
        "ivThrombolysisRationale": iv_thrombolysis_rationale,
        "thrombectomyRationale": thrombectomy_rationale,
        "anticoagulationTiming": anticoagulation_timing,
        "urgentFlags": urgent_flags,
        "treatmentPathway": treatment_pathway,
        "nextSteps": next_steps,
        "monitoringPlan": monitoring_plan,
        "evidenceLevel": evidence_level,
        "rationale": rationale,
        "references": _REFERENCES,
    }


def _n(x: float) -> str:
    """Render a parsed number the way JS template-literal interpolation would
    (integers without a trailing ``.0``)."""
    if x == int(x):
        return str(int(x))
    return str(x)
