"""PE Risk Classification Algorithm (2026 AHA/ACC clinical categories A-E).

Ported 1:1 from old_static_code/client/src/lib/peClassification.ts.

This is a plain helper library (NOT a registered engine): no LOGIC_KEY, no
``assess``. The fields are accessed by attribute name on a ``PatientData``-like
object (use the :func:`patient_data` helper to build one from a dict, or pass any
object/SimpleNamespace exposing the same attributes). The PatientData interface
field names are preserved exactly.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

# ---------------------------------------------------------------------------
# Input helper — build a PatientData-like namespace from a dict.
# Defaults mirror a healthy normotensive patient so missing keys do not crash;
# callers should supply real data.
# ---------------------------------------------------------------------------
_PATIENT_DEFAULTS: dict[str, Any] = {
    "name": "",
    "age": 0,
    "weight": 0,
    "heartRate": 0,
    "systolicBP": 0,
    "diastolicBP": 0,
    "respiratoryRate": 0,
    "spO2": 0,
    "temperature": 0,
    "symptomatic": False,
    "subsegmental": False,
    "rvDilation": False,
    "rvDysfunction": False,
    "tapse": None,
    "clotBurden": "low",
    "troponin": 0,
    "troponinElevated": False,
    "bnp": 0,
    "bnpElevated": False,
    "lactate": 0,
    "alteredMentalStatus": False,
    "needsVasopressors": False,
    "cardiacArrest": False,
    "syncope": False,
    "cancer": False,
    "heartFailure": False,
    "chronicLungDisease": False,
    "transientHypotension": False,
    "normotensiveShock": False,
    "persistentHypotension": False,
    "refractoryShock": False,
    "supplementalO2": False,
    "highFlowO2": False,
    "mechanicalVentilation": False,
    "recentSurgery": False,
    "recentStroke": False,
    "activeBleeding": False,
    "bleedingDiathesis": False,
    "intracranialNeoplasm": False,
    "recentHeadTrauma": False,
    "aorticDissection": False,
    "thrombocytopenia": False,
    "anticoagulantUse": False,
    "pregnancyOrPostpartum": False,
    "recentGIBleed": False,
    "uncontrolledHTN": False,
    "proximalDVT": False,
    "dvtLocation": "none",
    "dvtBilateral": False,
    "phlegmasia": False,
    "ivcFilterIndicated": False,
    "ivcFilterPlaced": False,
    "ivcFilterType": "none",
    "anticoagContraindication": False,
    "recurrentPEOnAnticoag": False,
}


def patient_data(data: dict) -> SimpleNamespace:
    """Build a PatientData-like namespace from a submitted dict.

    Missing keys fall back to neutral defaults so attribute access never
    raises. Note: this is a convenience constructor; the TS code passes a fully
    populated object.
    """
    merged = dict(_PATIENT_DEFAULTS)
    merged.update(data)
    return SimpleNamespace(**merged)


# ---------------------------------------------------------------------------
# sPESI Calculator
# ---------------------------------------------------------------------------
def calculate_spesi(data: Any) -> dict:
    score = 0
    details: list[str] = []
    if data.age > 80:
        score += 1
        details.append("Age > 80")
    if data.cancer:
        score += 1
        details.append("Active cancer")
    if data.heartFailure or data.chronicLungDisease:
        score += 1
        details.append("Cardiopulmonary disease")
    if data.heartRate >= 110:
        score += 1
        details.append("HR ≥ 110")
    if data.systolicBP < 100:
        score += 1
        details.append("SBP < 100 mmHg")
    if data.spO2 < 90:
        score += 1
        details.append("SpO2 < 90%")
    return {"score": score, "details": details}


# ---------------------------------------------------------------------------
# BOVA Score Calculator
# ---------------------------------------------------------------------------
def calculate_bova(data: Any) -> dict:
    score = 0
    details: list[str] = []
    if data.heartRate >= 110:
        score += 1
        details.append("HR ≥ 110 (+1)")
    if data.systolicBP < 90:
        score += 2
        details.append("SBP < 90 mmHg (+2)")
    elif data.systolicBP < 100:
        score += 2
        details.append("SBP 90-100 mmHg (+2)")
    tapse_abnormal = data.tapse is not None and data.tapse < 1.6
    if data.rvDysfunction or data.rvDilation or tapse_abnormal:
        tapse_note = f" [TAPSE {data.tapse} cm]" if tapse_abnormal else ""
        score += 2
        details.append(f"RV dysfunction (+2){tapse_note}")
    if data.troponinElevated:
        score += 2
        details.append("Elevated troponin (+2)")
    if score <= 2:
        stage = "Stage I (low risk)"
    elif score <= 4:
        stage = "Stage II (intermediate)"
    else:
        stage = "Stage III (high risk)"
    return {"score": score, "stage": stage, "details": details}


# ---------------------------------------------------------------------------
# NEWS Score Calculator
# ---------------------------------------------------------------------------
def calculate_news(data: Any) -> dict:
    score = 0
    details: list[str] = []

    if data.respiratoryRate <= 8:
        score += 3
        details.append("RR ≤8 (+3)")
    elif data.respiratoryRate <= 11:
        score += 1
        details.append("RR 9-11 (+1)")
    elif data.respiratoryRate <= 20:
        pass  # 0
    elif data.respiratoryRate <= 24:
        score += 2
        details.append("RR 21-24 (+2)")
    else:
        score += 3
        details.append("RR ≥25 (+3)")

    if data.spO2 <= 91:
        score += 3
        details.append("SpO2 ≤91% (+3)")
    elif data.spO2 <= 93:
        score += 2
        details.append("SpO2 92-93% (+2)")
    elif data.spO2 <= 95:
        score += 1
        details.append("SpO2 94-95% (+1)")

    if data.supplementalO2:
        score += 2
        details.append("On supplemental O2 (+2)")

    if data.temperature <= 35.0:
        score += 3
        details.append("Temp ≤35.0°C (+3)")
    elif data.temperature <= 36.0:
        score += 1
        details.append("Temp 35.1-36.0°C (+1)")
    elif data.temperature <= 38.0:
        pass  # 0
    elif data.temperature <= 39.0:
        score += 1
        details.append("Temp 38.1-39.0°C (+1)")
    else:
        score += 2
        details.append("Temp ≥39.1°C (+2)")

    if data.systolicBP <= 90:
        score += 3
        details.append("SBP ≤90 (+3)")
    elif data.systolicBP <= 100:
        score += 2
        details.append("SBP 91-100 (+2)")
    elif data.systolicBP <= 110:
        score += 1
        details.append("SBP 101-110 (+1)")
    elif data.systolicBP <= 219:
        pass  # 0
    else:
        score += 3
        details.append("SBP ≥220 (+3)")

    if data.heartRate <= 40:
        score += 3
        details.append("HR ≤40 (+3)")
    elif data.heartRate <= 50:
        score += 1
        details.append("HR 41-50 (+1)")
    elif data.heartRate <= 90:
        pass  # 0
    elif data.heartRate <= 110:
        score += 1
        details.append("HR 91-110 (+1)")
    elif data.heartRate <= 130:
        score += 2
        details.append("HR 111-130 (+2)")
    else:
        score += 3
        details.append("HR ≥131 (+3)")

    if data.alteredMentalStatus:
        score += 3
        details.append("Altered mental status (+3)")

    if score <= 4:
        risk = "Low"
    elif score <= 6:
        risk = "Medium"
    else:
        risk = "High"

    return {"score": score, "risk": risk, "details": details}


# ---------------------------------------------------------------------------
# Contraindication Assessment
# ---------------------------------------------------------------------------
def assess_contraindications(data: Any) -> dict:
    systolic_absolute: list[str] = []
    systolic_relative: list[str] = []
    cdt_absolute: list[str] = []
    cdt_relative: list[str] = []
    ac_cautions: list[str] = []

    if data.activeBleeding:
        systolic_absolute.append("Active bleeding")
        cdt_relative.append("Active bleeding (relative for CDT)")
        ac_cautions.append("Active bleeding — consider IVC filter")
    if data.recentStroke:
        systolic_absolute.append("Recent stroke (within 3 months)")
        cdt_relative.append("Recent stroke (use caution)")
    if data.intracranialNeoplasm:
        systolic_absolute.append("Intracranial neoplasm")
        cdt_absolute.append("Intracranial neoplasm")
    if data.recentHeadTrauma:
        systolic_absolute.append("Recent head trauma (within 3 weeks)")
        cdt_relative.append("Recent head trauma")
    if data.aorticDissection:
        systolic_absolute.append("Known/suspected aortic dissection")
        cdt_absolute.append("Aortic dissection")
    if data.recentSurgery:
        systolic_absolute.append("Recent major surgery (within 3 weeks)")
        cdt_relative.append("Recent surgery (proceed with caution, lower dose)")
    if data.bleedingDiathesis:
        systolic_relative.append("Known bleeding diathesis/coagulopathy")
        cdt_relative.append("Bleeding diathesis")
        ac_cautions.append("Bleeding diathesis — careful dosing, monitor closely")
    if data.thrombocytopenia:
        systolic_relative.append("Thrombocytopenia (platelets < 100k)")
        cdt_relative.append("Thrombocytopenia")
        ac_cautions.append("Thrombocytopenia — consider platelet transfusion threshold")
    if data.anticoagulantUse:
        systolic_relative.append("Already on therapeutic anticoagulation (INR > 1.7)")
        cdt_relative.append("Supratherapeutic anticoagulation")
    if data.pregnancyOrPostpartum:
        systolic_relative.append("Pregnancy or postpartum (within 1 week)")
        cdt_relative.append("Pregnancy/postpartum (multidisciplinary decision)")
        ac_cautions.append(
            "Pregnancy — DOACs contraindicated (Class 3: Harm), use LMWH or UFH only"
        )
    if data.recentGIBleed:
        systolic_relative.append("Recent GI bleeding (within 3 months)")
        cdt_relative.append("Recent GI bleeding")
        ac_cautions.append("Recent GI bleed — GI consultation recommended")
    if data.uncontrolledHTN:
        systolic_relative.append("Uncontrolled hypertension (SBP > 180)")
        cdt_relative.append("Uncontrolled hypertension")

    return {
        "systemicThrombolysis": {
            "eligible": len(systolic_absolute) == 0,
            "absolute": systolic_absolute,
            "relative": systolic_relative,
        },
        "cdt": {
            "eligible": len(cdt_absolute) == 0,
            "absolute": cdt_absolute,
            "relative": cdt_relative,
        },
        "anticoagulation": {
            "eligible": not data.activeBleeding,
            "cautions": ac_cautions,
        },
    }


# ---------------------------------------------------------------------------
# Respiratory Modifier (R)
# ---------------------------------------------------------------------------
def _assess_respiratory_modifier(data: Any, major_category: str) -> dict:
    if major_category == "C":
        triggers: list[str] = []
        if data.spO2 < 90:
            triggers.append("SpO₂ <90%")
        if data.respiratoryRate >= 30:
            triggers.append("RR ≥30")
        if data.supplementalO2:
            triggers.append("Needs supplemental O₂")
        return {"active": len(triggers) > 0, "detail": ", ".join(triggers)}
    if major_category == "D":
        triggers = []
        if data.highFlowO2:
            triggers.append(">6L nasal cannula or NRB mask")
        if data.supplementalO2 and not data.highFlowO2:
            triggers.append("On supplemental O₂")
        return {"active": len(triggers) > 0, "detail": ", ".join(triggers)}
    # E
    triggers = []
    if data.mechanicalVentilation:
        triggers.append("Hypoxemic respiratory failure or ventilatory failure")
    if data.highFlowO2 and not data.mechanicalVentilation:
        triggers.append(">6L nasal cannula or NRB mask")
    return {"active": len(triggers) > 0, "detail": ", ".join(triggers)}


# ---------------------------------------------------------------------------
# Main Classification Algorithm
# ---------------------------------------------------------------------------
def classify_pe(data: Any) -> dict:
    """Classify a PE patient into AHA/ACC 2026 category A-E.

    Accepts a PatientData-like object (attribute access). Build one from a dict
    with :func:`patient_data`.
    """
    spesi = calculate_spesi(data)
    bova = calculate_bova(data)
    news = calculate_news(data)
    scores = {
        "sPESI": dict(spesi),
        "BOVA": dict(bova),
        "NEWS": dict(news),
    }
    contraindications = assess_contraindications(data)
    lytics_safe = contraindications["systemicThrombolysis"]["eligible"]
    cdt_safe = contraindications["cdt"]["eligible"]

    tapse_abnormal = data.tapse is not None and data.tapse < 1.6
    has_abnormal_rv = data.rvDilation or data.rvDysfunction or tapse_abnormal
    has_abnormal_biomarker = data.troponinElevated or data.bnpElevated
    elevated_severity_score = spesi["score"] >= 1

    # ==================== Category A: Subclinical ====================
    if not data.symptomatic:
        return {
            "category": "A",
            "label": "Subclinical — Incidental and Asymptomatic",
            "riskLevel": "minimal",
            "respiratoryModifier": False,
            "respiratoryModifierDetail": "",
            "treatment": "Risk category consistent with populations in which anticoagulation has been studied. Consideration may be given to ED discharge without hospitalization in appropriate clinical context (Class 2a). Observation may be reasonable if isolated subsegmental with low clot burden.",
            "rationale": [
                "Incidental PE finding — patient is asymptomatic",
                "Risk-benefit of anticoagulation should be individualized",
                f"sPESI: {spesi['score']}",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §3.2", "finding": "Category A: Subclinical PE — patients can be safely discharged from the ED (Class 2a)", "year": 2026},
            ],
            "hemodynamicStatus": "stable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Not classified", "description": "Incidental/subclinical PE was not a distinct category in ESC 2019. Would generally be managed as low risk."},
        }

    # ==================== Category E2 ====================
    if data.refractoryShock or data.cardiacArrest:
        resp = _assess_respiratory_modifier(data, "E")
        treatment = "Risk category consistent with populations in which systemic thrombolysis has been studied (Class 2a). Consideration may be given to CDT/MT or VA-ECMO for circulatory support in appropriate clinical context. Surgical embolectomy not favored over other advanced options."
        if not lytics_safe and cdt_safe:
            treatment = "⚠️ Systemic lysis contraindicated — Consideration may be given to CDT/MT or VA-ECMO in appropriate clinical context. Urgent multidisciplinary PERT consultation recommended."
        elif not lytics_safe and not cdt_safe:
            treatment = "⚠️ Systemic lysis AND CDT contraindicated — Consideration may be given to VA-ECMO or surgical embolectomy in appropriate clinical context. Urgent multidisciplinary PERT consultation recommended."
        treatment += " ⚠️ AVOID deep sedation/intubation unless clinically necessary — cardiac arrest rates 19-28% after anesthesia induction in PE with RV dysfunction (Class 3: Harm)."
        return {
            "category": "E2",
            "label": "Cardiopulmonary Failure — Refractory Shock / Cardiac Arrest",
            "riskLevel": "critical",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": treatment,
            "rationale": [
                "Cardiac arrest" if data.cardiacArrest else "Refractory cardiogenic shock",
                "Immediate intervention required — activate PERT (Class 1, Level B-NR)",
                f"NEWS score: {news['score']} ({news['risk']})",
                f"Lactate: {data.lactate} mmol/L (Class 1 recommendation to measure)",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Category E2: Systemic thrombolysis is reasonable. Surgical embolectomy not recommended over VA-ECMO.", "year": 2026},
                {"source": "2026 AHA/ACC PE Guidelines §4.2.3", "finding": "Deep sedation and mechanical ventilation — Class 3: Harm unless clinically necessary in Categories C-E", "year": 2026},
                {"source": "STORM PE Trial", "finding": "Demonstrated feasibility of CDT in massive PE when systemic therapy contraindicated", "year": 2023},
            ],
            "hemodynamicStatus": "unstable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "High Risk", "description": "ESC 2019 High Risk (Massive PE): Hemodynamic instability with cardiac arrest or sustained hypotension requiring vasopressors."},
        }

    # ==================== Category E1 ====================
    if data.persistentHypotension or (data.needsVasopressors and data.systolicBP < 90):
        resp = _assess_respiratory_modifier(data, "E")
        treatment = "Risk category consistent with populations in which advanced therapies have been studied (Class 2a). Consideration may be given to systemic thrombolysis, CDT, MT, or surgical embolectomy in appropriate clinical context. Anticoagulation with LMWH preferred over UFH (Class 1). PERT activation recommended."
        if not lytics_safe and cdt_safe:
            treatment = "⚠️ Systemic lysis contraindicated — Consideration may be given to CDT/MT or surgical embolectomy in appropriate clinical context (Class 2a). Anticoagulation + vasopressor support."
        elif not lytics_safe and not cdt_safe:
            treatment = "⚠️ Lysis & CDT contraindicated — Consideration may be given to surgical embolectomy or VA-ECMO in appropriate clinical context. Urgent multidisciplinary PERT consultation recommended."
        treatment += " ⚠️ AVOID deep sedation unless clinically necessary (Class 3: Harm)."
        rationale = [
            "Recurrent or persistent hypotension with cardiogenic shock",
            f"SBP {data.systolicBP} mmHg",
            "Requiring vasopressor support" if data.needsVasopressors else "",
            "Activate PERT (Class 1, Level B-NR)",
            f"NEWS score: {news['score']} ({news['risk']})",
            f"Lactate: {data.lactate} mmol/L (Class 1 to measure for Cat C-E)",
        ]
        return {
            "category": "E1",
            "label": "Cardiopulmonary Failure — Persistent Hypotension with Cardiogenic Shock",
            "riskLevel": "critical",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": treatment,
            "rationale": [r for r in rationale if r],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Category E1: Systemic thrombolysis, CDT, MT, or surgical embolectomy are reasonable (Class 2a)", "year": 2026},
                {"source": "PEERLESS Trial", "finding": "CDT vs MT: no significant difference in 30-day mortality or major bleeding (550 patients)", "year": 2024},
            ],
            "hemodynamicStatus": "unstable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "High Risk", "description": "ESC 2019 High Risk (Massive PE): Hemodynamic instability with persistent hypotension or shock."},
        }

    # ==================== Category D1 ====================
    if data.transientHypotension:
        resp = _assess_respiratory_modifier(data, "D")
        treatment = "Hospitalization to ICU is generally appropriate. Anticoagulation (LMWH > UFH, Class 1). Risk category consistent with populations in which advanced therapies have been studied (Class 2b). Consideration may be given to systemic thrombolysis, CDT, or MT in appropriate clinical context. PERT activation recommended (Class 1)."
        if not lytics_safe and cdt_safe:
            treatment = "⚠️ Systemic lysis contraindicated — Consideration may be given to CDT/MT in appropriate clinical context (Class 2b). Anticoagulation + ICU monitoring. PERT activation recommended."
        elif not lytics_safe and not cdt_safe:
            treatment = "⚠️ Lysis & CDT contraindicated — Anticoagulation + ICU monitoring. Surgical consultation may be appropriate if clinical deterioration occurs. PERT activation recommended."
        treatment += " ⚠️ AVOID deep sedation unless clinically necessary (Class 3: Harm)."
        return {
            "category": "D1",
            "label": "Incipient Cardiopulmonary Failure — Transient Hypotension",
            "riskLevel": "high",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": treatment,
            "rationale": [
                "Transient hypotension (SBP <90 that resolved)",
                f"Current SBP: {data.systolicBP} mmHg",
                "RV dysfunction/dilation present" if has_abnormal_rv else "RV assessment recommended (echo preferred, Class 1)",
                "Activate PERT (Class 1, Level B-NR)",
                f"NEWS score: {news['score']} ({news['risk']})",
                f"Lactate: {data.lactate} mmol/L",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Categories D1-D2: Advanced therapies may be considered (Class 2b)", "year": 2026},
                {"source": "2026 AHA/ACC PE Guidelines §3.2", "finding": "Lactate measurement is Class 1 for Categories C-E", "year": 2026},
            ],
            "hemodynamicStatus": "unstable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Intermediate-High Risk", "description": "ESC 2019 Intermediate-High Risk: Transient hypotension that resolved — patient is currently hemodynamically stable. ESC 2019 reserved 'High Risk' for sustained hypotension (>15 min) or cardiac arrest. The 2026 AHA/ACC created Category D to specifically capture these 'incipient failure' patients."},
        }

    # ==================== Category D2 ====================
    if data.normotensiveShock:
        resp = _assess_respiratory_modifier(data, "D")
        treatment = "Hospitalization to ICU is generally appropriate. Anticoagulation (LMWH > UFH, Class 1). Risk category consistent with populations in which advanced therapies have been studied (Class 2b). Consideration may be given to systemic thrombolysis, CDT, or MT in appropriate clinical context. PERT activation recommended (Class 1)."
        if not cdt_safe and not lytics_safe:
            treatment = "⚠️ Lysis & CDT contraindicated — Anticoagulation + ICU monitoring. Surgical consultation may be appropriate if clinical deterioration occurs. PERT activation recommended."
        elif not lytics_safe:
            treatment = "⚠️ Systemic lysis contraindicated — Consideration may be given to CDT/MT in appropriate clinical context (Class 2b). Anticoagulation + ICU. PERT activation recommended."
        treatment += " ⚠️ AVOID deep sedation unless clinically necessary (Class 3: Harm)."
        rationale = [
            "Normotensive shock — organ hypoperfusion despite normal blood pressure",
            f"SBP: {data.systolicBP} mmHg (normal range but end-organ dysfunction present)",
            f"Lactate: {data.lactate} mmol/L",
            "RV dysfunction/dilation present" if has_abnormal_rv else "",
            "Altered mental status" if data.alteredMentalStatus else "",
            "Activate PERT (Class 1, Level B-NR)",
        ]
        return {
            "category": "D2",
            "label": "Incipient Cardiopulmonary Failure — Normotensive Shock",
            "riskLevel": "high",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": treatment,
            "rationale": [r for r in rationale if r],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Categories D1-D2: Advanced therapies may be considered (Class 2b)", "year": 2026},
                {"source": "2026 AHA/ACC PE Guidelines §7.1.4", "finding": "PERT is recommended to improve timeliness of care (Class 1, Level B-NR)", "year": 2026},
            ],
            "hemodynamicStatus": "unstable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Intermediate-High Risk", "description": "ESC 2019 Intermediate-High Risk: Normotensive with signs of organ hypoperfusion. The 2026 AHA/ACC reclassifies this as 'incipient cardiopulmonary failure' due to occult shock."},
        }

    # ==================== Category B ====================
    if not elevated_severity_score:
        if data.subsegmental:
            return {
                "category": "B1",
                "label": "Symptomatic — Subsegmental PE",
                "riskLevel": "low",
                "respiratoryModifier": False,
                "respiratoryModifierDetail": "",
                "treatment": "Risk category consistent with populations in which anticoagulation with DOACs has been studied (Class 1). Early discharge may be appropriate in suitable clinical context (Class 2a). Surveillance without anticoagulation may be reasonable if isolated subsegmental, no proximal DVT, and low bleeding risk.",
                "rationale": [
                    "Symptomatic PE with low clinical severity (sPESI = 0)",
                    "Subsegmental clot location",
                    "Early discharge/outpatient management reasonable using Hestia, PESI, or sPESI (Class 2a)",
                    f"sPESI: {spesi['score']}",
                ],
                "scores": scores,
                "evidence": [
                    {"source": "2026 AHA/ACC PE Guidelines §4.1.1", "finding": "Category B: Early discharge generally recommended (Class 2a). HOME-PE trial validated Hestia and sPESI equally.", "year": 2026},
                    {"source": "2026 AHA/ACC PE Guidelines §4.2.1", "finding": "DOACs recommended over VKA (Class 1, Level B-R). LMWH recommended over UFH (Class 1, Level B-R).", "year": 2026},
                ],
                "hemodynamicStatus": "stable",
                "contraindications": contraindications,
                "esc2019Equivalent": {"category": "Low Risk", "description": "ESC 2019 Low Risk: sPESI 0 or PESI class I-II, hemodynamically stable, no RV dysfunction or biomarker elevation."},
            }
        return {
            "category": "B2",
            "label": "Symptomatic — Non-Subsegmental PE, Low Severity",
            "riskLevel": "low",
            "respiratoryModifier": False,
            "respiratoryModifierDetail": "",
            "treatment": "Risk category consistent with populations in which anticoagulation with DOACs has been studied (Class 1). Early discharge may be appropriate in suitable clinical context (Class 2a) using Hestia/sPESI/PESI criteria.",
            "rationale": [
                "Symptomatic PE with low clinical severity (sPESI = 0)",
                "Non-subsegmental clot location",
                "Outpatient management reasonable per HOME-PE trial (Hestia and sPESI performed equally)",
                f"sPESI: {spesi['score']}",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.1.1", "finding": "Category B: Early discharge generally recommended (Class 2a). HOME-PE trial validates outpatient management.", "year": 2026},
                {"source": "2026 AHA/ACC PE Guidelines §4.2.1", "finding": "DOACs recommended over VKA (Class 1). LMWH over UFH if parenteral needed (Class 1).", "year": 2026},
                {"source": "Hestia Criteria", "finding": "Validated criteria for identifying PE patients safe for outpatient management", "year": 2011},
            ],
            "hemodynamicStatus": "stable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Low Risk", "description": "ESC 2019 Low Risk: sPESI 0 or PESI class I-II, hemodynamically stable, suitable for early discharge."},
        }

    # ==================== Category C ====================
    resp = _assess_respiratory_modifier(data, "C")

    # C3
    if has_abnormal_rv and has_abnormal_biomarker:
        high_lactate = data.lactate >= 2.0
        additional_risk = high_lactate or data.syncope or bova["score"] >= 5
        treatment = "Hospitalization is generally appropriate. Anticoagulation (LMWH > UFH, Class 1; DOACs > VKA, Class 1). Role of systemic thrombolysis and catheter-based therapies remains unclear at this category level. Close ICU monitoring may be warranted. PERT activation recommended (Class 1)."
        if additional_risk:
            treatment = "Hospitalization to ICU is generally appropriate. Anticoagulation (LMWH > UFH, Class 1; DOACs > VKA, Class 1). Role of advanced therapies remains unclear — risks and benefits should be weighed carefully with PERT. Escalation plan may be warranted if deterioration to Category D/E."
        treatment += " Note: Systemic thrombolysis and CDT/MT — benefit unclear at C3 level (PEITHO: prevented collapse but increased bleeding/ICH)."
        if not cdt_safe:
            treatment += " ⚠️ CDT contraindicated — weigh surgical consultation if clinical deterioration."
        elif len(contraindications["cdt"]["relative"]) > 0:
            treatment += " ⚠️ Relative contraindications to CDT present."
        treatment += " ⚠️ AVOID deep sedation unless clinically necessary (Class 3: Harm)."
        return {
            "category": "C3",
            "label": "Symptomatic, Elevated Severity — Abnormal RV AND Abnormal Biomarker",
            "riskLevel": "moderate",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": treatment,
            "rationale": [
                "Abnormal RV AND ≥1 abnormal biomarker — highest risk within Category C",
                f"sPESI: {spesi['score']} (elevated) | BOVA: {bova['score']} ({bova['stage']})",
                f"Troponin elevated: {'Yes' if data.troponinElevated else 'No'} | BNP elevated: {'Yes' if data.bnpElevated else 'No'}",
                f"Lactate: {data.lactate} mmol/L{' (elevated)' if high_lactate else ''} — Class 1 to measure",
                "High clot burden on CT" if data.clotBurden == "high" else f"Clot burden: {data.clotBurden}",
                "RV imaging recommended — echo preferred over CT (Class 1)",
                "Activate PERT (Class 1, Level B-NR)",
                "Additional risk factors — close monitoring for deterioration to Category D" if additional_risk else "Monitor closely for deterioration",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Category C3: Role of systemic thrombolysis and catheter-based therapies is unclear. Systemic thrombolysis is harmful for A-C2 (Class 3: Harm).", "year": 2026},
                {"source": "PEITHO Trial", "finding": "Thrombolysis in intermediate-risk PE prevented cardiovascular collapse but increased major bleeding including intracranial hemorrhage", "year": 2014},
                {"source": "HI-PEITHO Trial", "finding": "Ultrasound-facilitated CDT reduced RV/LV ratio vs anticoagulation alone without increasing major bleeding", "year": 2024},
                {"source": "PEERLESS Trial", "finding": "CDT vs MT: no significant difference in 30-day mortality or major bleeding", "year": 2024},
                {"source": "BOVA Score Validation", "finding": f"BOVA {bova['stage']} — 30-day PE-related complication rate correlates with score", "year": 2016},
            ],
            "hemodynamicStatus": "stable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Intermediate-High Risk", "description": "ESC 2019 Intermediate-High Risk (Submassive PE): RV dysfunction AND elevated cardiac biomarkers in a hemodynamically stable patient. PESI class III-V or sPESI ≥1."},
        }

    # C2
    if has_abnormal_rv or has_abnormal_biomarker:
        return {
            "category": "C2",
            "label": "Symptomatic, Elevated Severity — Abnormal RV or Abnormal Biomarker",
            "riskLevel": "moderate",
            "respiratoryModifier": resp["active"],
            "respiratoryModifierDetail": resp["detail"],
            "treatment": "Hospitalization is generally appropriate. Anticoagulation (LMWH > UFH, Class 1; DOACs > VKA, Class 1). This category is consistent with populations in which systemic thrombolysis was associated with harm (Class 3: Harm). CDT/MT not supported by current evidence. Telemetry monitoring is generally appropriate. PERT activation recommended (Class 1).",
            "rationale": [
                "Abnormal RV but biomarkers not elevated" if has_abnormal_rv else "Abnormal biomarker(s) without RV dysfunction",
                f"sPESI: {spesi['score']} (elevated) | BOVA: {bova['score']} ({bova['stage']})",
                f"Lactate: {data.lactate} mmol/L — Class 1 to measure",
                "Systemic thrombolysis harmful at this level (Class 3: Harm)",
                "CDT/MT not recommended",
                "RV imaging recommended — echo preferred over CT (Class 1)",
                "Activate PERT for Categories C-E (Class 1)",
            ],
            "scores": scores,
            "evidence": [
                {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Categories A-C2: Systemic thrombolysis is harmful (Class 3: Harm). CDT and MT are not recommended.", "year": 2026},
                {"source": "2026 AHA/ACC PE Guidelines §4.2.1", "finding": "DOACs recommended over VKA (Class 1). LMWH over UFH (Class 1).", "year": 2026},
            ],
            "hemodynamicStatus": "stable",
            "contraindications": contraindications,
            "esc2019Equivalent": {"category": "Intermediate-Low Risk", "description": "ESC 2019 Intermediate-Low Risk: RV dysfunction OR elevated biomarkers (but not both) in a hemodynamically stable patient."},
        }

    # C1
    return {
        "category": "C1",
        "label": "Symptomatic, Elevated Severity — Normal RV and Normal Biomarkers",
        "riskLevel": "low",
        "respiratoryModifier": resp["active"],
        "respiratoryModifierDetail": resp["detail"],
        "treatment": "Hospitalization is generally appropriate. Anticoagulation (DOACs > VKA, Class 1; LMWH > UFH if parenteral needed, Class 1). This category is consistent with populations in which systemic thrombolysis was associated with harm (Class 3: Harm). CDT/MT not supported by current evidence. Monitoring for clinical deterioration is recommended.",
        "rationale": [
            "Elevated clinical severity score but normal RV and normal biomarkers",
            f"sPESI: {spesi['score']} (elevated)",
            "No RV dysfunction or dilation",
            "Normal cardiac biomarkers",
            "Systemic thrombolysis harmful at this level (Class 3: Harm)",
            "Activate PERT for Categories C-E (Class 1)",
        ],
        "scores": scores,
        "evidence": [
            {"source": "2026 AHA/ACC PE Guidelines §4.4", "finding": "Categories A-C2: Systemic thrombolysis is harmful (Class 3: Harm). CDT and MT are not recommended.", "year": 2026},
            {"source": "2026 AHA/ACC PE Guidelines §4.1.2", "finding": "Category C: Hospitalization recommended to optimize treatment strategies", "year": 2026},
        ],
        "hemodynamicStatus": "stable",
        "contraindications": contraindications,
        "esc2019Equivalent": {"category": "Intermediate-Low Risk", "description": "ESC 2019 Intermediate-Low Risk: Elevated severity score (sPESI ≥1) but no RV dysfunction and normal biomarkers."},
    }
