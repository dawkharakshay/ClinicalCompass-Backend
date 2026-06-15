"""ECMO Candidacy Assessment for Massive Pulmonary Embolism.

Ported 1:1 from old_static_code/client/src/lib/ecmoCandidacy.ts.

Plain helper library (no LOGIC_KEY, no ``assess``). Imports the PatientData /
classification shapes from :mod:`app.recommendations.shared.pe_classification`.

The ECMOAssessmentInput is represented as an attribute-bearing object (build one
with :func:`ecmo_input` or :func:`create_default_ecmo_input`). The
``classificationResult`` is the dict returned by ``classify_pe``; it is accessed
with subscript (``["category"]`` etc.) to match that return shape.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from app.recommendations.shared.pe_classification import (  # noqa: F401  (re-export)
    classify_pe,
    patient_data,
)

# ---------------------------------------------------------------------------
# ECMOAssessmentInput helper
# ---------------------------------------------------------------------------
_ECMO_DEFAULTS: dict[str, Any] = {
    "preECMOCardiacArrest": False,
    "diastolicBP6h": 0,
    "pulsePressure6h": 0,
    "peakInspiratoryPressure": 0,
    "intubationDurationHours": 0,
    "hco3": 0,
    "acuteRenalFailure": False,
    "chronicRenalFailure": False,
    "liverFailure": False,
    "cnsDysfunction": False,
    "unwitnessedArrest": False,
    "prolongedCPROver60Min": False,
    "terminalIllness": False,
    "advancedAge": False,
    "severeBaselineFunctionalImpairment": False,
    "uncontrolledBleeding": False,
    "irreversibleNeurologicalInjury": False,
    "severePVD": False,
    "aorticRegurgitation": False,
}


def ecmo_input(patient_data_obj: Any, classification_result: dict, **fields: Any) -> SimpleNamespace:
    """Build an ECMOAssessmentInput-like namespace.

    ``patient_data_obj`` is a PatientData-like object; ``classification_result``
    is the dict from :func:`classify_pe`. Remaining ECMO-specific fields default
    to neutral values unless supplied.
    """
    merged = dict(_ECMO_DEFAULTS)
    merged.update(fields)
    merged["patientData"] = patient_data_obj
    merged["classificationResult"] = classification_result
    return SimpleNamespace(**merged)


# ---------------------------------------------------------------------------
# SAVE Score Calculation
# ---------------------------------------------------------------------------
def calculate_save_score(inp: Any) -> dict:
    score = 0
    details: list[str] = []
    age = inp.patientData.age
    weight = inp.patientData.weight

    # Age
    if 18 <= age <= 38:
        score += 7
        details.append(f"Age {age} (18-38): +7")
    elif 39 <= age <= 52:
        score += 4
        details.append(f"Age {age} (39-52): +4")
    elif 53 <= age <= 62:
        score += 3
        details.append(f"Age {age} (53-62): +3")
    else:
        score += 0
        details.append(f"Age {age} (≥63): +0")

    # Weight (kg)
    if weight < 65:
        score += 1
        details.append(f"Weight {weight}kg (<65): +1")
    elif weight <= 89:
        score += 2
        details.append(f"Weight {weight}kg (65-89): +2")
    else:
        score += 0
        details.append(f"Weight {weight}kg (>89): +0")

    # Cause of cardiogenic shock — PE (no additional modifier)
    details.append("Cause: Acute PE (no additional modifier)")

    # Renal
    if inp.chronicRenalFailure:
        score -= 6
        details.append("Chronic renal failure: -6")
    elif inp.acuteRenalFailure:
        score -= 3
        details.append("Acute renal failure: -3")

    # Metabolic acidosis
    if inp.hco3 <= 15:
        score -= 3
        details.append(f"HCO₃ {inp.hco3} (≤15): -3")

    # Intubation duration
    if inp.intubationDurationHours >= 30:
        score -= 4
        details.append(f"Intubation {inp.intubationDurationHours}h (≥30): -4")
    elif inp.intubationDurationHours >= 11:
        score -= 2
        details.append(f"Intubation {inp.intubationDurationHours}h (11-29): -2")
    else:
        details.append(f"Intubation {inp.intubationDurationHours}h (≤10): +0")

    # Peak inspiratory pressure
    if inp.peakInspiratoryPressure <= 20:
        score += 3
        details.append(f"PIP {inp.peakInspiratoryPressure} (≤20): +3")

    # Pre-ECMO cardiac arrest
    if inp.preECMOCardiacArrest:
        score -= 2
        details.append("Pre-ECMO cardiac arrest: -2")

    # Diastolic BP ≥40 within 6h
    if inp.diastolicBP6h >= 40:
        score += 3
        details.append(f"DBP {inp.diastolicBP6h} (≥40): +3")

    # Pulse pressure ≤20
    if inp.pulsePressure6h <= 20:
        score -= 2
        details.append(f"Pulse pressure {inp.pulsePressure6h} (≤20): -2")

    # Organ failures
    if inp.liverFailure:
        score -= 3
        details.append("Liver failure: -3")
    if inp.cnsDysfunction:
        score -= 3
        details.append("CNS dysfunction: -3")

    # Lactate <8.3 mmol/L
    if inp.patientData.lactate < 8.3:
        score += 15
        details.append(f"Lactate {inp.patientData.lactate} (<8.3 mmol/L): +15")

    # Risk class
    if score >= 5:
        risk_class = "I (Low Risk)"
        predicted_survival = "~75%"
    elif score >= 1:
        risk_class = "II"
        predicted_survival = "~58%"
    elif score >= -4:
        risk_class = "III"
        predicted_survival = "~42%"
    elif score >= -9:
        risk_class = "IV"
        predicted_survival = "~30%"
    else:
        risk_class = "V (High Risk)"
        predicted_survival = "<20%"

    return {
        "score": score,
        "riskClass": risk_class,
        "predictedSurvival": predicted_survival,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Indications Assessment
# ---------------------------------------------------------------------------
def _assess_indications(inp: Any) -> list[dict]:
    cat = inp.classificationResult["category"]
    d = inp.patientData

    return [
        {
            "label": "Cardiac arrest due to PE (ECPR)",
            "present": d.cardiacArrest,
            "strength": "strong",
            "source": "Kmiec et al. 2020; ELSO Guidelines",
        },
        {
            "label": "Refractory cardiogenic shock despite vasopressors",
            "present": d.refractoryShock or (d.needsVasopressors and d.systolicBP < 90),
            "strength": "strong",
            "source": "AHA JAHA 2024; Kmiec et al. 2020",
        },
        {
            "label": "Persistent hemodynamic instability despite initial therapies",
            "present": d.persistentHypotension and d.needsVasopressors,
            "strength": "strong",
            "source": "ESC 2019; AHA 2026 Cat E1",
        },
        {
            "label": "Contraindication to systemic thrombolysis",
            "present": not inp.classificationResult["contraindications"]["systemicThrombolysis"]["eligible"],
            "strength": "moderate",
            "source": "Kmiec et al. 2020; Pavlovic et al. 2014",
        },
        {
            "label": "Failed thrombolysis with ongoing hemodynamic compromise",
            "present": False,
            "strength": "strong",
            "source": "ELSO Guidelines; AHA JAHA 2024",
        },
        {
            "label": "Severe RV dysfunction with hemodynamic instability",
            "present": d.rvDysfunction and (d.systolicBP < 90 or d.needsVasopressors),
            "strength": "strong",
            "source": "AHA JAHA 2024; 2026 AHA/ACC Guidelines",
        },
        {
            "label": "Severe hypoxemic respiratory failure (SpO₂ <85% despite max O₂)",
            "present": d.spO2 < 85 and d.mechanicalVentilation,
            "strength": "moderate",
            "source": "Kmiec et al. 2020 (VV-ECMO consideration)",
        },
        {
            "label": "PE category E1 or E2 (AHA/ACC 2026)",
            "present": cat == "E1" or cat == "E2",
            "strength": "strong",
            "source": "2026 AHA/ACC PE Guidelines §4.4",
        },
        {
            "label": "Lactate ≥4 mmol/L with hemodynamic compromise",
            "present": d.lactate >= 4 and (d.systolicBP < 90 or d.needsVasopressors),
            "strength": "moderate",
            "source": "George et al. 2017 (lactate ≤6 mmol/L predictive of survival)",
        },
    ]


# ---------------------------------------------------------------------------
# Contraindications Assessment
# ---------------------------------------------------------------------------
def _assess_ecmo_contraindications(inp: Any) -> list[dict]:
    return [
        {
            "label": "Unwitnessed cardiac arrest with prolonged downtime",
            "present": inp.unwitnessedArrest,
            "type": "absolute",
            "source": "ELSO Guidelines",
        },
        {
            "label": "Prolonged CPR >60 minutes without ROSC",
            "present": inp.prolongedCPROver60Min,
            "type": "absolute",
            "source": "ELSO Guidelines; Scott et al. 2021",
        },
        {
            "label": "Pre-existing terminal illness or poor life expectancy",
            "present": inp.terminalIllness,
            "type": "absolute",
            "source": "ELSO Guidelines",
        },
        {
            "label": "Irreversible neurological injury",
            "present": inp.irreversibleNeurologicalInjury,
            "type": "absolute",
            "source": "ELSO Guidelines",
        },
        {
            "label": "Severe baseline functional impairment",
            "present": inp.severeBaselineFunctionalImpairment,
            "type": "absolute",
            "source": "ELSO Guidelines",
        },
        {
            "label": "Uncontrolled bleeding",
            "present": inp.uncontrolledBleeding,
            "type": "relative",
            "source": "ELSO Guidelines (heparinization required for ECMO circuit)",
        },
        {
            "label": "Advanced age (>75 years)",
            "present": inp.advancedAge or inp.patientData.age > 75,
            "type": "relative",
            "source": "Institution-dependent; ELSO registry data",
        },
        {
            "label": "Severe peripheral vascular disease (limits cannulation)",
            "present": inp.severePVD,
            "type": "relative",
            "source": "Technical consideration for peripheral cannulation",
        },
        {
            "label": "Significant aortic regurgitation",
            "present": inp.aorticRegurgitation,
            "type": "relative",
            "source": "VA-ECMO increases LV afterload; may worsen AR",
        },
    ]


# ---------------------------------------------------------------------------
# ECMO Configuration Recommendation
# ---------------------------------------------------------------------------
def _recommend_config(inp: Any) -> dict:
    d = inp.patientData

    if d.cardiacArrest or d.refractoryShock:
        return {
            "config": "VA-ECMO",
            "rationale": "VA-ECMO is the preferred configuration for cardiac arrest or refractory shock due to PE. It unloads the RV and improves oxygenation simultaneously (Kmiec et al. 2020; AHA JAHA 2024).",
        }

    if d.persistentHypotension or d.needsVasopressors:
        return {
            "config": "VA-ECMO",
            "rationale": "VA-ECMO addresses both hemodynamic instability and gas exchange abnormalities in persistent hypotension/cardiogenic shock (AHA JAHA 2024).",
        }

    if (not d.needsVasopressors) and d.systolicBP >= 90 and d.mechanicalVentilation and d.spO2 < 88:
        return {
            "config": "VA-ECMO (with VV consideration)",
            "rationale": "Patient has stable circulation but severe respiratory failure. VV-ECMO may be considered if hemodynamics remain stable without high-dose vasopressors. VA-ECMO remains the safer default (Kmiec et al. 2020: VV-ECMO survival 45% vs VA-ECMO 48%, p=0.9).",
        }

    return {
        "config": "VA-ECMO",
        "rationale": "VA-ECMO is the standard configuration for PE-related MCS, addressing pulmonary circulation and gas exchange abnormalities (AHA JAHA 2024).",
    }


# ---------------------------------------------------------------------------
# Overall Candidacy Assessment
# ---------------------------------------------------------------------------
def assess_ecmo_candidacy(inp: Any) -> dict:
    indications = _assess_indications(inp)
    contraindications = _assess_ecmo_contraindications(inp)
    save_score = calculate_save_score(inp)
    rc = _recommend_config(inp)
    config = rc["config"]
    config_rationale = rc["rationale"]

    present_indications = [i for i in indications if i["present"]]
    strong_indications = [i for i in present_indications if i["strength"] == "strong"]
    absolute_contra = [c for c in contraindications if c["present"] and c["type"] == "absolute"]
    relative_contra = [c for c in contraindications if c["present"] and c["type"] == "relative"]

    candidacy_rationale: list[str] = []

    if len(absolute_contra) > 0:
        candidacy = "not_candidate"
        candidacy_label = "Not a Candidate"
        candidacy_rationale.append(
            "Absolute contraindication(s): " + "; ".join(c["label"] for c in absolute_contra)
        )
        if len(present_indications) > 0:
            candidacy_rationale.append(
                f"Note: {len(present_indications)} indication(s) present but overridden by absolute contraindication(s)"
            )
    elif len(strong_indications) > 0 and len(relative_contra) == 0:
        candidacy = "candidate"
        candidacy_label = "ECMO Candidate"
        candidacy_rationale.append(
            f"{len(strong_indications)} strong indication(s) present with no contraindications"
        )
        candidacy_rationale.append(
            f"SAVE score: {save_score['score']} — Risk Class {save_score['riskClass']}, predicted survival {save_score['predictedSurvival']}"
        )
    elif len(present_indications) > 0:
        candidacy = "conditional"
        candidacy_label = "Conditional Candidate"
        if len(relative_contra) > 0:
            candidacy_rationale.append(
                "Relative contraindication(s): " + "; ".join(c["label"] for c in relative_contra)
            )
        candidacy_rationale.append(
            f"{len(present_indications)} indication(s) present — multidisciplinary evaluation recommended"
        )
        candidacy_rationale.append(
            f"SAVE score: {save_score['score']} — Risk Class {save_score['riskClass']}, predicted survival {save_score['predictedSurvival']}"
        )
    else:
        candidacy = "not_candidate"
        candidacy_label = "Not Indicated"
        candidacy_rationale.append("No ECMO indications identified based on current clinical presentation")
        candidacy_rationale.append("ECMO is generally reserved for massive PE (AHA/ACC Categories E1/E2) or refractory cases")

    # Prognostic factors
    key_prognostic_factors: list[str] = []
    if inp.patientData.lactate <= 6:
        key_prognostic_factors.append(
            f"Lactate {inp.patientData.lactate} mmol/L (≤6): favorable prognostic sign (82.4% sensitivity, 84.6% specificity for survival — George et al.)"
        )
    else:
        key_prognostic_factors.append(
            f"Lactate {inp.patientData.lactate} mmol/L (>6): associated with worse outcomes"
        )
    if inp.preECMOCardiacArrest:
        key_prognostic_factors.append(
            "Pre-ECMO cardiac arrest: associated with higher mortality (Yusuff et al. OR 16.71, p=0.0004)"
        )
    if inp.patientData.cancer:
        key_prognostic_factors.append(
            "Active malignancy: nonsurvivors tended to have history of malignancy (George et al.)"
        )

    references = [
        {"source": "Kmiec et al. ASAIO J. 2020;66(2):146-152", "finding": "ECMO feasible for initial stabilization as bridge to therapy in massive PE. VA-ECMO survival 48%, VV-ECMO 45% (p=0.9). Additional interventions (thrombectomy) vs anticoagulation alone showed similar survival (44% vs 49%, p=0.40).", "year": 2020},
        {"source": "AHA JAHA Review: MCS for Massive PE", "finding": "VA-ECMO preferred for massive PE — unloads RV, improves oxygenation. Overall systematic review survival >60%. SAVE score and SOFA-RV useful for prognostication.", "year": 2024},
        {"source": "Schmidt et al. Eur Heart J. 2015;36:2246-56", "finding": "SAVE score predicts survival on VA-ECMO. Score ≥5 associated with ~75% survival; ≤-10 with >80% mortality.", "year": 2015},
        {"source": "George et al. J Card Surg. 2018;33:269-74", "finding": "Lactate ≤6 mmol/L: 82.4% sensitivity and 84.6% specificity for predicting survival to discharge on VA-ECMO for PE.", "year": 2018},
        {"source": "Pasrija et al. Ann Thorac Surg. 2018;105:440-6", "finding": "Protocolized VA-ECMO approach for massive PE showed 96% 1-year survival vs 73% with historical surgical approach (p=0.02).", "year": 2018},
        {"source": "Scott et al. Resuscitation. 2022;173:1-10", "finding": "ECPR for PE-related cardiac arrest: 61% survived to discharge, 88% neurologically intact.", "year": 2022},
    ]

    return {
        "candidacy": candidacy,
        "candidacyLabel": candidacy_label,
        "candidacyRationale": candidacy_rationale,
        "indications": indications,
        "contraindications": contraindications,
        "saveScore": save_score,
        "recommendedConfig": "Not recommended" if candidacy == "not_candidate" else config,
        "configRationale": "ECMO not recommended based on current assessment" if candidacy == "not_candidate" else config_rationale,
        "keyPrognosticFactors": key_prognostic_factors,
        "references": references,
    }


# ---------------------------------------------------------------------------
# Default ECMO input from existing patient data
# ---------------------------------------------------------------------------
def create_default_ecmo_input(patient_data_obj: Any, classification_result: dict) -> SimpleNamespace:
    pd = patient_data_obj
    return SimpleNamespace(
        patientData=pd,
        classificationResult=classification_result,
        preECMOCardiacArrest=pd.cardiacArrest,
        diastolicBP6h=pd.diastolicBP,
        pulsePressure6h=pd.systolicBP - pd.diastolicBP,
        peakInspiratoryPressure=25 if pd.mechanicalVentilation else 15,
        intubationDurationHours=0,
        hco3=22,  # default normal
        acuteRenalFailure=False,
        chronicRenalFailure=False,
        liverFailure=False,
        cnsDysfunction=pd.alteredMentalStatus,
        unwitnessedArrest=False,
        prolongedCPROver60Min=False,
        terminalIllness=False,
        advancedAge=pd.age > 75,
        severeBaselineFunctionalImpairment=False,
        uncontrolledBleeding=pd.activeBleeding,
        irreversibleNeurologicalInjury=False,
        severePVD=False,
        aorticRegurgitation=False,
    )
