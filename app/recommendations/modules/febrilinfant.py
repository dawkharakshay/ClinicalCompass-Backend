"""Febrile Infant Evaluation Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/febrilInfantLogic.ts
(assessFebrilInfant). AAP Clinical Practice Guideline 2021 (updated 2025) /
PECARN 2019.
"""

from __future__ import annotations

from app.recommendations.jslib import truthy

LOGIC_KEY = "febrilinfant"

_REF_AAP = {
    "citation": "Pantell RH et al. Evaluation and Management of Well-Appearing Febrile Infants 8 to 60 Days Old. Pediatrics. 2021;148(2):e2021052228.",
    "url": "https://publications.aap.org/pediatrics/article/148/2/e2021052228",
}
_REF_PECARN = {
    "citation": "Kuppermann N et al. A Clinical Prediction Rule to Identify Febrile Infants at Low Risk for Serious Bacterial Infection. JAMA. 2019;322(18):1765–1776. (PECARN)",
    "url": "https://jamanetwork.com/journals/jama/fullarticle/2755184",
}


def _js_str(v) -> str:
    """Render a value the way TS template literals do (true/false/null)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    return str(v)


def assess(data: dict) -> dict:
    age_group = data.get("ageGroup")
    age_days = data.get("ageDays")
    temperature_celsius = data.get("temperatureCelsius")
    well_appearing = data.get("wellAppearing")
    hsv_risk_factors = data.get("hsvRiskFactors")
    has_seizures = data.get("hasSeizures")
    has_skin_lesions = data.get("hasSkinLesions")
    has_eye_discharge = data.get("hasEyeDischarge")

    urgent_flags: list[str] = []
    workup: list[str] = []

    # ─── HSV risk ───────────────────────────────────────────────────────────
    if (
        truthy(hsv_risk_factors)
        or truthy(has_seizures)
        or truthy(has_skin_lesions)
        or truthy(has_eye_discharge)
    ):
        urgent_flags.append(
            "HSV RISK: Obtain HSV PCR (blood + CSF + surface swabs). Initiate acyclovir 20mg/kg IV q8h empirically. Do NOT delay treatment pending results."
        )

    # ─── Age 0–7 days ───────────────────────────────────────────────────────
    if age_group == "0_7_days":
        urgent_flags.append(
            "NEONATE (0–7 days): Full sepsis evaluation + empiric antibiotics + ADMISSION required regardless of appearance."
        )
        workup.extend(
            [
                "CBC with differential",
                "Blood culture × 2",
                "Urinalysis + urine culture (catheterized)",
                "Lumbar puncture (CSF cell count, protein, glucose, culture, HSV PCR)",
                "CRP and procalcitonin",
                "Chest X-ray if respiratory symptoms",
                "HSV surface swabs (eye, nasopharynx, rectum)",
            ]
        )
        return {
            "primaryRecommendation": "NEONATE FEVER (0–7 days): ADMIT + FULL SEPSIS WORKUP + EMPIRIC ANTIBIOTICS. Ampicillin + gentamicin ± cefotaxime. Add acyclovir if HSV risk.",
            "riskCategory": "very_high",
            "workupRequired": workup,
            "admissionDecision": "ADMIT to NICU or inpatient pediatrics. Full sepsis evaluation mandatory.",
            "antibioticRecommendation": "Ampicillin 50mg/kg IV q6h + Gentamicin 4mg/kg IV q24h. Add cefotaxime 50mg/kg IV q6h if meningitis suspected. Acyclovir 20mg/kg IV q8h if HSV risk.",
            "hsvManagement": "HSV surface swabs + HSV PCR (blood + CSF). Empiric acyclovir 20mg/kg IV q8h until HSV excluded.",
            "urgentFlags": urgent_flags,
            "dispositionPlan": "ADMIT to NICU or inpatient pediatrics. Minimum 48-hour observation pending cultures.",
            "followUpPlan": "Cultures at 24–48 hours. Adjust antibiotics per sensitivities. Repeat LP if initial CSF traumatic.",
            "evidenceLevel": "A",
            "rationale": f"Neonate {_js_str(age_days)} days. Temperature {_js_str(temperature_celsius)}°C. Full workup mandatory per AAP 2021 CPG.",
            "references": [_REF_AAP],
        }

    # ─── Age 8–28 days ──────────────────────────────────────────────────────
    if age_group in ("8_21_days", "22_28_days"):
        urgent_flags.append(
            f"HIGH-RISK AGE GROUP ({_js_str(age_days)} days): Full sepsis evaluation + empiric antibiotics + ADMISSION strongly recommended."
        )
        workup.extend(
            [
                "CBC with differential + ANC",
                "Blood culture",
                "Urinalysis + urine culture (catheterized)",
                "Lumbar puncture (CSF analysis + culture + HSV PCR)",
                "CRP and procalcitonin",
                "Chest X-ray if respiratory symptoms",
            ]
        )
        return {
            "primaryRecommendation": f"FEBRILE INFANT {_js_str(age_days)} DAYS: ADMIT + FULL WORKUP + EMPIRIC ANTIBIOTICS. Risk stratification possible at 22–28 days but admission still preferred.",
            "riskCategory": "high",
            "workupRequired": workup,
            "admissionDecision": "ADMIT. Empiric antibiotics after cultures obtained. LP should not be deferred.",
            "antibioticRecommendation": "Ampicillin 50mg/kg IV q6h + Cefotaxime 50mg/kg IV q6h (or gentamicin if cefotaxime unavailable). Acyclovir 20mg/kg IV q8h if HSV risk.",
            "hsvManagement": (
                "HSV RISK PRESENT: Acyclovir 20mg/kg IV q8h empirically. HSV PCR blood + CSF + surface swabs."
                if (truthy(hsv_risk_factors) or truthy(has_seizures) or truthy(has_skin_lesions))
                else "Low HSV risk. Obtain HSV PCR from CSF at time of LP. Acyclovir not required unless risk factors present."
            ),
            "urgentFlags": urgent_flags,
            "dispositionPlan": "ADMIT to inpatient pediatrics. 48-hour observation minimum.",
            "followUpPlan": "Blood and urine cultures at 24–48 hours. Adjust antibiotics per sensitivities. Discontinue antibiotics if cultures negative and well-appearing at 48 hours.",
            "evidenceLevel": "A",
            "rationale": f"Age {_js_str(age_days)} days. Temperature {_js_str(temperature_celsius)}°C. Well-appearing: {_js_str(well_appearing)}. Per AAP 2021 CPG.",
            "references": [_REF_AAP],
        }

    # ─── Age 29–60 days — PECARN/AAP risk stratification ─────────────────────
    workup.extend(
        [
            "Urinalysis + urine culture (catheterized) — MANDATORY",
            "CBC with differential",
            "Blood culture",
            "CRP and/or procalcitonin",
        ]
    )

    risk_category = "intermediate"
    admission_decision: str
    antibiotic_rec: str
    disposition_plan: str

    anc = data.get("absoluteNeutrophilCount")
    procal = data.get("procalcitonin")
    crp = data.get("cReactiveProtein")
    urinalysis_positive = data.get("urinalysisPositive")

    anc_low = anc is not None and anc < 4090
    procal_low = procal is not None and procal < 0.5
    crp_low = crp is not None and crp < 20  # noqa: F841 (mirrors TS; unused downstream)
    ua_positive = urinalysis_positive is True

    if not truthy(well_appearing):
        risk_category = "high"
        urgent_flags.append(
            "ILL-APPEARING INFANT: Full sepsis workup + empiric antibiotics + ADMISSION regardless of lab values."
        )
        admission_decision = "ADMIT. Ill-appearing infant — full workup mandatory."
        antibiotic_rec = "Ceftriaxone 50mg/kg IV/IM q24h (or ampicillin + cefotaxime). Add acyclovir if HSV risk."
        disposition_plan = "ADMIT to inpatient pediatrics."
        workup.append("Lumbar puncture (CSF analysis + culture + HSV PCR)")
    elif data.get("pecarnLowRisk") is True and not ua_positive and anc_low and procal_low:
        risk_category = "low"
        admission_decision = "LOW RISK: Outpatient management acceptable IF reliable follow-up within 24 hours AND urine culture pending. No LP required per PECARN criteria."
        antibiotic_rec = "Antibiotics NOT required if low risk and well-appearing. If empiric treatment chosen: ceftriaxone 50mg/kg IM single dose with 24-hour follow-up."
        disposition_plan = "DISCHARGE with strict return precautions. Follow-up in 24 hours. Urine culture must be followed."
    elif ua_positive and not anc_low:
        risk_category = "intermediate"
        admission_decision = "INTERMEDIATE RISK: LP recommended. Admit vs. discharge with empiric antibiotics based on clinical judgment and family reliability."
        antibiotic_rec = "Ceftriaxone 50mg/kg IV/IM. If UTI source: continue ceftriaxone pending culture. LP recommended before antibiotics if meningitis not excluded."
        disposition_plan = "Admit for observation OR discharge with empiric ceftriaxone + 24-hour follow-up if LP negative and reliable family."
        workup.append("Lumbar puncture recommended (AAP 2021 — intermediate risk)")
    else:
        risk_category = "intermediate"
        admission_decision = "INTERMEDIATE RISK: Clinical judgment required. LP recommended. Admit vs. discharge per clinical assessment."
        antibiotic_rec = "Ceftriaxone 50mg/kg IV/IM after LP. Adjust per culture results."
        disposition_plan = "Admit for observation OR discharge with empiric ceftriaxone + 24-hour follow-up."
        workup.append("Lumbar puncture recommended")

    hsv_management = (
        "HSV RISK PRESENT: Acyclovir 20mg/kg IV q8h empirically. HSV PCR (blood + CSF + surface swabs). Ophthalmology consult for eye lesions."
        if (
            truthy(hsv_risk_factors)
            or truthy(has_seizures)
            or truthy(has_skin_lesions)
            or truthy(has_eye_discharge)
        )
        else "Low HSV risk at 29–60 days. Acyclovir not routinely indicated unless risk factors present."
    )

    if len(urgent_flags) > 0:
        primary_rec = urgent_flags[0]
    else:
        primary_rec = (
            f"FEBRILE INFANT {_js_str(age_days)} DAYS — {risk_category.upper()} RISK. "
            f"Temperature {_js_str(temperature_celsius)}°C. {admission_decision.split(':')[0]}."
        )

    return {
        "primaryRecommendation": primary_rec,
        "riskCategory": risk_category,
        "workupRequired": workup,
        "admissionDecision": admission_decision,
        "antibioticRecommendation": antibiotic_rec,
        "hsvManagement": hsv_management,
        "urgentFlags": urgent_flags,
        "dispositionPlan": disposition_plan,
        "followUpPlan": (
            "Mandatory 24-hour follow-up. Return immediately for fever recurrence, ill appearance, or positive culture result."
            if risk_category == "low"
            else "Follow-up per inpatient course. Cultures at 24–48 hours. Adjust antibiotics per sensitivities."
        ),
        "evidenceLevel": "A",
        "rationale": (
            f"Age {_js_str(age_days)} days. Temp {_js_str(temperature_celsius)}°C. "
            f"Well-appearing: {_js_str(well_appearing)}. "
            f"ANC: {_js_str(anc) if anc is not None else 'not obtained'}. "
            f"PCT: {_js_str(procal) if procal is not None else 'not obtained'}. "
            f"UA positive: {_js_str(urinalysis_positive)}. "
            f"PECARN low risk: {_js_str(data.get('pecarnLowRisk'))}. "
            "Per AAP 2021 CPG and PECARN 2019."
        ),
        "references": [_REF_AAP, _REF_PECARN],
    }
