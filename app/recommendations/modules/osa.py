"""Obstructive Sleep Apnea (OSA) Clinical Compass.

Ported 1:1 from old_static_code/client/src/lib/osaLogic.ts (assessOSA and its
helpers classifyOSASeverity, getSeverityLabel, calculateCVRisk, isHNSEligible,
isOralApplianceSuitable).

Based on:
 - AASM Clinical Practice Guideline: Treatment of OSA in Adults 2024 (PMID: 38692572)
 - AAO-HNS Clinical Practice Guideline: Adult Snoring 2019 (PMID: 30920341)
 - STAR Trial: Inspire HNS (PMID: 24401051)
"""

from __future__ import annotations

import math

from app.recommendations.jslib import parse_float, truthy

LOGIC_KEY = "osa"


def _num(x) -> float:
    """parseFloat-like read that preserves a literal 0 (NaN -> 0).

    The TS code reads these fields as plain ``number`` and never uses the
    ``|| default`` idiom on them, so 0 must be preserved (unlike jslib.num).
    """
    v = parse_float(x)
    return 0.0 if math.isnan(v) else v


def _fmt(x: float) -> str:
    """Mirror JS number-to-string for the interpolated AHI/BMI values."""
    if x == int(x):
        return str(int(x))
    return repr(x)


def classify_osa_severity(ahi: float) -> str:
    if ahi < 15:
        return "mild"
    if ahi < 30:
        return "moderate"
    return "severe"


def get_severity_label(ahi: float) -> str:
    if ahi < 5:
        return "Normal (<5 events/hour)"
    if ahi < 15:
        return f"Mild OSA (AHI {_fmt(ahi)} events/hour)"
    if ahi < 30:
        return f"Moderate OSA (AHI {_fmt(ahi)} events/hour)"
    return f"Severe OSA (AHI {_fmt(ahi)} events/hour)"


def calculate_cv_risk(data: dict) -> dict:
    ahi = _num(data.get("ahi"))
    min_o2 = _num(data.get("minO2Sat"))
    cv_conditions = sum(
        1
        for c in (
            truthy(data.get("hypertension")),
            truthy(data.get("afib")),
            truthy(data.get("heartFailure")),
            truthy(data.get("stroke")),
        )
        if c
    )
    severity = classify_osa_severity(ahi)
    if cv_conditions >= 2 or truthy(data.get("stroke")) or truthy(data.get("heartFailure")):
        return {
            "risk": "high",
            "rationale": "High CV risk: established cardiovascular disease + OSA — CPAP reduces MACE risk (meta-analysis: OR 0.65 for recurrent stroke)",
        }
    if cv_conditions >= 1 or severity == "severe" or min_o2 < 80:
        return {
            "risk": "moderate",
            "rationale": "Moderate CV risk: OSA with cardiovascular comorbidity or severe hypoxemia — CPAP treatment strongly recommended",
        }
    return {
        "risk": "low",
        "rationale": "Low-moderate CV risk: OSA without established cardiovascular disease",
    }


def is_hns_eligible(data: dict) -> dict:
    ahi = _num(data.get("ahi"))
    bmi = _num(data.get("bmi"))
    cpap_adherence = data.get("cpapAdherence")
    criteria: list[str] = []
    contraindications: list[str] = []
    eligible = True

    # AHI criteria: 15-65 per AASM 2024
    if ahi >= 15 and ahi <= 100:
        criteria.append(f"AHI {_fmt(ahi)} (eligible range: 15-100 per AASM 2024)")
    else:
        contraindications.append(
            f"AHI {_fmt(ahi)}: outside optimal range (15-100) — discuss with sleep surgeon"
        )
        if ahi < 15:
            eligible = False

    # CPAP failure required
    if cpap_adherence == "non_adherent" or cpap_adherence == "intolerant":
        criteria.append("CPAP failure/intolerance confirmed")
    elif cpap_adherence == "naive":
        contraindications.append("CPAP naive: CPAP trial required before HNS per AASM 2024")
        eligible = False

    # BMI criteria
    if bmi < 32:
        criteria.append(f"BMI {_fmt(bmi)} (optimal: <32)")
    elif bmi < 40:
        criteria.append(f"BMI {_fmt(bmi)} (acceptable: 32-40, reduced efficacy)")
    else:
        contraindications.append(
            f"BMI {_fmt(bmi)} ≥40: significantly reduced HNS efficacy — weight loss recommended first"
        )
        eligible = False

    # No complete concentric collapse at palate (DISE required)
    contraindications.append(
        "Drug-induced sleep endoscopy (DISE) required to rule out complete concentric collapse (CCC) at palate — CCC is a contraindication to HNS"
    )

    # Central component
    if truthy(data.get("centralComponent")):
        contraindications.append("Significant central sleep apnea: HNS not indicated for central events")
        eligible = False

    return {"eligible": eligible, "criteria": criteria, "contraindications": contraindications}


def is_oral_appliance_suitable(data: dict) -> bool:
    ahi = _num(data.get("ahi"))
    cpap_adherence = data.get("cpapAdherence")
    if data.get("anatomicObstruction") == "retrognathia":
        return False
    if truthy(data.get("centralComponent")):
        return False
    return ahi <= 30 or cpap_adherence == "non_adherent" or cpap_adherence == "intolerant"


def assess(data: dict) -> dict:
    ahi = _num(data.get("ahi"))
    min_o2 = _num(data.get("minO2Sat"))
    ess = _num(data.get("ess"))
    tonsil_size = _num(data.get("tonsilSize"))
    cpap_adherence = data.get("cpapAdherence")
    anatomic = data.get("anatomicObstruction")

    severity = classify_osa_severity(ahi)
    severity_label = get_severity_label(ahi)
    cv_risk_result = calculate_cv_risk(data)
    hns_result = is_hns_eligible(data)
    oral_appliance_suitable = is_oral_appliance_suitable(data)
    warnings: list[str] = []
    next_steps: list[str] = []

    # Warnings
    if truthy(data.get("afib")):
        warnings.append(
            "Atrial fibrillation: OSA treatment reduces AF recurrence after cardioversion (meta-analysis: OR 0.58) — CPAP strongly recommended"
        )
    if truthy(data.get("heartFailure")):
        warnings.append(
            "Heart failure: OSA treatment improves LVEF and quality of life — CPAP or ASV (if central apneas predominate) recommended"
        )
    if truthy(data.get("stroke")):
        warnings.append(
            "Prior stroke: OSA treatment reduces recurrent stroke risk — CPAP strongly recommended"
        )
    if truthy(data.get("pregnant")):
        warnings.append(
            "Pregnancy: OSA associated with gestational hypertension, preeclampsia, and fetal growth restriction — CPAP strongly recommended"
        )
    if min_o2 < 80:
        warnings.append(
            "Severe nocturnal hypoxemia (min O2 <80%): urgent CPAP initiation recommended — high cardiovascular risk"
        )
    if truthy(data.get("depression")):
        warnings.append(
            "Depression: OSA treatment improves depressive symptoms — screen for treatment-resistant depression in untreated OSA"
        )
    if truthy(data.get("centralComponent")):
        warnings.append(
            "Central sleep apnea component: adaptive servo-ventilation (ASV) may be required — avoid ASV if EF <45% (SERVE-HF trial)"
        )

    # ── Mild OSA with low symptoms ──
    if (
        severity == "mild"
        and ess < 10
        and not truthy(data.get("afib"))
        and not truthy(data.get("heartFailure"))
        and not truthy(data.get("stroke"))
    ):
        next_steps.append(
            "Lifestyle modifications: weight loss (10% weight loss reduces AHI by ~26%), alcohol avoidance, sleep position optimization"
        )
        if truthy(data.get("positionalOSA")):
            next_steps.append(
                "Positional therapy: avoid supine sleep — positional device (NightBalance) or tennis ball technique"
            )
        next_steps.append("Repeat sleep study in 6-12 months if symptoms worsen")
        positional = truthy(data.get("positionalOSA"))
        return {
            "primaryTreatment": "positional_therapy" if positional else "weight_loss",
            "primaryLabel": "Positional Therapy + Lifestyle Modification"
            if positional
            else "Lifestyle Modification (Weight Loss, Sleep Hygiene)",
            "alternativeTreatments": ["oral_appliance", "cpap_first_line"],
            "alternativeLabels": [
                "Oral Appliance Therapy (MAD)",
                "CPAP (if symptoms worsen or patient prefers)",
            ],
            "cpapRecommendation": "CPAP optional for mild OSA — offer if patient symptomatic or prefers active treatment",
            "hnsEligible": False,
            "hnsCriteria": [],
            "hnsContraindications": ["Mild OSA: HNS not indicated"],
            "oralApplianceSuitable": True,
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "Mild OSA with minimal symptoms: lifestyle modification is first-line per AASM 2024. CPAP or oral appliance offered if patient prefers active treatment.",
            "evidenceLevel": "Moderate",
            "guidelineSource": "AASM 2024 (PMID: 38692572)",
        }

    # ── CPAP naive — first-line CPAP ──
    if cpap_adherence == "naive":
        next_steps.append("Initiate CPAP therapy: auto-CPAP (APAP) preferred for initial titration")
        next_steps.append(
            "CPAP education and mask fitting — proper mask interface critical for adherence"
        )
        next_steps.append(
            "Follow-up at 1 month: assess adherence (≥4 hours/night, ≥70% nights), residual AHI, and symptoms"
        )
        next_steps.append(
            "Address CPAP side effects: mask leak, claustrophobia, aerophagia — early intervention improves adherence"
        )
        if truthy(data.get("positionalOSA")):
            next_steps.append("Positional therapy as adjunct to CPAP")
        titration = "Severe OSA: consider in-lab titration PSG." if ahi >= 30 else ""
        return {
            "primaryTreatment": "cpap_first_line",
            "primaryLabel": "CPAP Therapy (First-Line — Auto-CPAP/APAP)",
            "alternativeTreatments": ["oral_appliance"] if oral_appliance_suitable else [],
            "alternativeLabels": ["Oral Appliance (MAD) — if CPAP not tolerated"]
            if oral_appliance_suitable
            else [],
            "cpapRecommendation": f"Auto-CPAP (APAP): starting range 5-20 cmH2O. Titrate to residual AHI <5. {titration}",
            "hnsEligible": False,
            "hnsCriteria": [],
            "hnsContraindications": ["CPAP naive: CPAP trial required before HNS"],
            "oralApplianceSuitable": oral_appliance_suitable,
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "CPAP is the gold standard first-line treatment for moderate-severe OSA and symptomatic mild OSA per AASM 2024. APAP is equivalent to fixed CPAP for most patients.",
            "evidenceLevel": "Strong",
            "guidelineSource": "AASM 2024 (PMID: 38692572)",
        }

    # ── CPAP adherent ──
    if cpap_adherence == "adherent":
        next_steps.append("Continue CPAP therapy — ensure residual AHI <5 on device data")
        next_steps.append("Annual follow-up: reassess symptoms, weight, and device compliance data")
        next_steps.append("If residual AHI >5: consider CPAP pressure adjustment or switch to BiPAP")
        return {
            "primaryTreatment": "cpap_optimization",
            "primaryLabel": "Continue and Optimize CPAP Therapy",
            "alternativeTreatments": [],
            "alternativeLabels": [],
            "cpapRecommendation": "Continue current CPAP — optimize pressure if residual AHI >5. Consider BiPAP if high pressures required (>15 cmH2O).",
            "hnsEligible": False,
            "hnsCriteria": [],
            "hnsContraindications": ["CPAP adherent: HNS not indicated"],
            "oralApplianceSuitable": False,
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "CPAP adherent patients: continue and optimize therapy. Annual follow-up recommended.",
            "evidenceLevel": "Strong",
            "guidelineSource": "AASM 2024 (PMID: 38692572)",
        }

    # ── CPAP non-adherent or intolerant ──
    # HNS (Inspire) — preferred surgical option for moderate-severe OSA
    if hns_result["eligible"] and (severity == "moderate" or severity == "severe"):
        next_steps.append(
            "Drug-induced sleep endoscopy (DISE) to rule out complete concentric collapse (CCC) at palate"
        )
        next_steps.append(
            "HNS (Inspire) implantation: outpatient procedure, activation at 1 month post-implant"
        )
        next_steps.append("Post-implant: titration PSG at 2-3 months, then annual follow-up")
        next_steps.append(
            "Expected outcomes: 70-80% responder rate (AHI reduction ≥50% and AHI <20)"
        )
        return {
            "primaryTreatment": "hns_inspire",
            "primaryLabel": "Hypoglossal Nerve Stimulation (HNS / Inspire) — Preferred Surgical Option",
            "alternativeTreatments": ["oral_appliance", "surgical_uppp"]
            if oral_appliance_suitable
            else ["surgical_uppp", "surgical_mma"],
            "alternativeLabels": [
                "Oral Appliance (MAD) — if HNS not eligible",
                "UPPP ± palatal procedures (multilevel surgery)",
            ]
            if oral_appliance_suitable
            else [
                "UPPP ± multilevel surgery",
                "MMA (maxillomandibular advancement) — for retrognathia or failed UPPP",
            ],
            "hnsEligible": True,
            "hnsCriteria": hns_result["criteria"],
            "hnsContraindications": hns_result["contraindications"],
            "oralApplianceSuitable": oral_appliance_suitable,
            "surgicalProcedure": "Hypoglossal Nerve Stimulation (Inspire Medical Systems)",
            "surgicalRationale": "STAR trial: 68% responder rate, 78% reduction in AHI, 70% reduction in ODI at 12 months. EFFECT trial: HNS non-inferior to CPAP for moderate-severe OSA.",
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "HNS (Inspire) is the preferred surgical treatment for CPAP-intolerant moderate-severe OSA without complete concentric collapse. STAR trial: 68% responder rate. EFFECT trial: non-inferior to CPAP.",
            "evidenceLevel": "Strong",
            "guidelineSource": "AASM 2024 (PMID: 38692572); STAR Trial (PMID: 24401051)",
        }

    # Oral appliance for mild-moderate or CPAP intolerant
    if oral_appliance_suitable and (severity == "mild" or severity == "moderate"):
        next_steps.append(
            "Mandibular advancement device (MAD): custom-fitted by dental sleep medicine specialist"
        )
        next_steps.append(
            "Titration: advance 0.5-1 mm every 1-2 weeks to maximum tolerable position"
        )
        next_steps.append(
            "Follow-up sleep study with MAD in place to confirm efficacy (AHI <5 or ≥50% reduction)"
        )
        return {
            "primaryTreatment": "oral_appliance",
            "primaryLabel": "Oral Appliance Therapy (Mandibular Advancement Device)",
            "alternativeTreatments": ["hns_inspire", "surgical_uppp"],
            "alternativeLabels": [
                "HNS (Inspire) — if moderate OSA and CPAP intolerant",
                "UPPP — if palatal obstruction identified",
            ],
            "hnsEligible": hns_result["eligible"],
            "hnsCriteria": hns_result["criteria"],
            "hnsContraindications": hns_result["contraindications"],
            "oralApplianceSuitable": True,
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": [
                *warnings,
                "Oral appliance efficacy: inferior to CPAP for severe OSA — confirm efficacy with follow-up sleep study",
                "Side effects: temporomandibular joint pain, tooth soreness — monitor and adjust",
            ],
            "nextSteps": next_steps,
            "rationale": "Oral appliance (MAD) is recommended for mild-moderate OSA or CPAP-intolerant patients. Efficacy: 50-60% responder rate. Inferior to CPAP for severe OSA.",
            "evidenceLevel": "Strong",
            "guidelineSource": "AASM 2024 (PMID: 38692572)",
        }

    # Surgical options for CPAP intolerant with anatomic obstruction
    if anatomic == "palatal" and tonsil_size >= 3:
        next_steps.append(
            "Tonsillectomy + UPPP: most effective for large tonsils (grade 3-4) with palatal obstruction"
        )
        next_steps.append("Pre-operative DISE to confirm palatal obstruction pattern")
        return {
            "primaryTreatment": "surgical_tonsillectomy",
            "primaryLabel": "Tonsillectomy + UPPP (Large Tonsils, Palatal Obstruction)",
            "alternativeTreatments": ["hns_inspire", "oral_appliance"],
            "alternativeLabels": [
                "HNS (Inspire) — if DISE shows no CCC",
                "Oral Appliance (MAD)",
            ],
            "hnsEligible": hns_result["eligible"],
            "hnsCriteria": hns_result["criteria"],
            "hnsContraindications": hns_result["contraindications"],
            "oralApplianceSuitable": oral_appliance_suitable,
            "surgicalProcedure": "Tonsillectomy + Uvulopalatopharyngoplasty (UPPP)",
            "surgicalRationale": "Tonsillectomy + UPPP: 60-80% success rate for grade 3-4 tonsils. Most effective surgical option for palatal obstruction with large tonsils.",
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": warnings,
            "nextSteps": next_steps,
            "rationale": "Tonsillectomy + UPPP is recommended for CPAP-intolerant OSA with grade 3-4 tonsils and palatal obstruction. Success rate 60-80%.",
            "evidenceLevel": "Moderate",
            "guidelineSource": "AAO-HNS 2019 (PMID: 30920341); AASM 2024 (PMID: 38692572)",
        }

    # MMA for retrognathia or failed UPPP
    if anatomic == "retrognathia" or truthy(data.get("priorUPPP")):
        next_steps.append(
            "Maxillomandibular advancement (MMA): most effective surgical procedure for OSA — 85-90% success rate"
        )
        next_steps.append("Pre-operative cephalometry and orthodontic evaluation")
        next_steps.append("Requires 6-8 week jaw wiring — significant recovery period")
        return {
            "primaryTreatment": "surgical_mma",
            "primaryLabel": "Maxillomandibular Advancement (MMA) — Highest Surgical Success Rate",
            "alternativeTreatments": ["hns_inspire", "oral_appliance"],
            "alternativeLabels": [
                "HNS (Inspire) — if DISE eligible",
                "Oral Appliance (MAD)",
            ],
            "hnsEligible": hns_result["eligible"],
            "hnsCriteria": hns_result["criteria"],
            "hnsContraindications": hns_result["contraindications"],
            "oralApplianceSuitable": oral_appliance_suitable,
            "surgicalProcedure": "Maxillomandibular Advancement (MMA)",
            "surgicalRationale": "MMA: 85-90% success rate (AHI reduction ≥50%), most effective surgical procedure for OSA. Indicated for retrognathia or failed UPPP.",
            "severityLabel": severity_label,
            "cvRisk": cv_risk_result["risk"],
            "cvRiskRationale": cv_risk_result["rationale"],
            "keyWarnings": [
                *warnings,
                "MMA: significant surgical procedure with 6-8 week recovery — ensure patient is well-informed",
            ],
            "nextSteps": next_steps,
            "rationale": "MMA is the most effective surgical procedure for OSA (85-90% success rate). Indicated for retrognathia or failed UPPP.",
            "evidenceLevel": "Strong",
            "guidelineSource": "AASM 2024 (PMID: 38692572); AAO-HNS 2019 (PMID: 30920341)",
        }

    # Default: combination therapy / multidisciplinary
    return {
        "primaryTreatment": "combination_therapy",
        "primaryLabel": "Combination Therapy (CPAP + Adjunctive Measures)",
        "alternativeTreatments": ["hns_inspire", "oral_appliance"],
        "alternativeLabels": [
            "HNS (Inspire) — if CPAP intolerant and eligible",
            "Oral Appliance (MAD)",
        ],
        "cpapRecommendation": "Re-trial CPAP with improved adherence support: desensitization protocol, cognitive behavioral therapy for CPAP, different mask interface",
        "hnsEligible": hns_result["eligible"],
        "hnsCriteria": hns_result["criteria"],
        "hnsContraindications": hns_result["contraindications"],
        "oralApplianceSuitable": oral_appliance_suitable,
        "severityLabel": severity_label,
        "cvRisk": cv_risk_result["risk"],
        "cvRiskRationale": cv_risk_result["rationale"],
        "keyWarnings": warnings,
        "nextSteps": [
            "Sleep medicine referral for comprehensive OSA management",
            "CPAP re-trial with behavioral support and mask optimization",
            "Weight loss: 10% weight loss reduces AHI by ~26%",
            "Consider HNS (Inspire) evaluation if CPAP intolerant",
        ],
        "rationale": "Complex OSA management: combination therapy and multidisciplinary approach recommended.",
        "evidenceLevel": "Moderate",
        "guidelineSource": "AASM 2024 (PMID: 38692572)",
    }
