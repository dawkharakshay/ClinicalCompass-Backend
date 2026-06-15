"""Tests for ECMO Candidacy — authored from the TS branches in
old_static_code/client/src/lib/ecmoCandidacy.ts (no server test exists for the
candidacy logic; ecmo.state.test.ts only covers Base64 state encoding).
"""

from __future__ import annotations

import pytest

from app.recommendations.shared.ecmo_candidacy import (
    assess_ecmo_candidacy,
    calculate_save_score,
    create_default_ecmo_input,
    ecmo_input,
)
from app.recommendations.shared.pe_classification import classify_pe, patient_data
from tests.recommendations.test_pe_classification import BASE


def pt(**overrides):
    d = dict(BASE)
    d.update(overrides)
    return patient_data(d)


# ---- SAVE score ----
def test_save_score_young_light_low_lactate():
    # age 45 -> +4 (39-52); weight 70 -> +2 (65-89); PIP 15 -> +3 (<=20);
    # DBP 80 -> +3 (>=40); pulse pressure 40 -> not <=20; hco3 22 -> not <=15;
    # lactate 1.0 -> +15. Total = 4+2+3+3+15 = 27.
    p = pt()
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = calculate_save_score(inp)
    assert r["score"] == 27
    assert r["riskClass"] == "I (Low Risk)"
    assert r["predictedSurvival"] == "~75%"


def test_save_score_penalties():
    # age 70 -> +0 (>=63); weight 70 -> +2; chronicRenalFailure -6; hco3 10 -> -3;
    # intubation 35h -> -4; PIP 30 -> not <=20; preECMO arrest -2; DBP 30 -> not >=40;
    # pulse pressure 10 -> -2; liver -3; cns -3; lactate 5 -> +15.
    # Total = 0+2-6-3-4-2-2-3-3+15 = -6
    p = pt(age=70, weight=70, lactate=5)
    cls = classify_pe(p)
    inp = ecmo_input(
        p, cls,
        preECMOCardiacArrest=True,
        diastolicBP6h=30,
        pulsePressure6h=10,
        peakInspiratoryPressure=30,
        intubationDurationHours=35,
        hco3=10,
        chronicRenalFailure=True,
        liverFailure=True,
        cnsDysfunction=True,
    )
    r = calculate_save_score(inp)
    assert r["score"] == -6
    assert r["riskClass"] == "IV"


# ---- Candidacy: candidate (strong indication, no contra) ----
def test_candidate_cardiac_arrest():
    p = pt(cardiacArrest=True, refractoryShock=True, systolicBP=60)
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    assert r["candidacy"] == "candidate"
    assert r["candidacyLabel"] == "ECMO Candidate"
    assert r["recommendedConfig"] == "VA-ECMO"


# ---- Candidacy: not_candidate via absolute contraindication ----
def test_not_candidate_absolute_contra():
    p = pt(cardiacArrest=True, refractoryShock=True, systolicBP=60)
    cls = classify_pe(p)
    inp = ecmo_input(
        p, cls,
        preECMOCardiacArrest=True,
        diastolicBP6h=60,
        pulsePressure6h=40,
        peakInspiratoryPressure=25,
        prolongedCPROver60Min=True,
    )
    r = assess_ecmo_candidacy(inp)
    assert r["candidacy"] == "not_candidate"
    assert r["candidacyLabel"] == "Not a Candidate"
    assert r["recommendedConfig"] == "Not recommended"
    assert r["configRationale"] == "ECMO not recommended based on current assessment"
    assert any("overridden by absolute" in s for s in r["candidacyRationale"])


# ---- Candidacy: conditional (indication + relative contra) ----
def test_conditional_with_relative_contra():
    # E1 patient (strong indication) but advanced age >75 -> relative contra
    p = pt(persistentHypotension=True, needsVasopressors=True, systolicBP=80, age=80)
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    assert r["candidacy"] == "conditional"
    assert r["candidacyLabel"] == "Conditional Candidate"
    assert any("Relative contraindication" in s for s in r["candidacyRationale"])


# ---- Candidacy: not_candidate / Not Indicated (no indications) ----
def test_not_indicated_stable_patient():
    p = pt()  # B2 stable, no indications
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    assert r["candidacy"] == "not_candidate"
    assert r["candidacyLabel"] == "Not Indicated"
    assert r["recommendedConfig"] == "Not recommended"


# ---- Config: VV consideration ----
def test_config_vv_consideration():
    p = pt(mechanicalVentilation=True, spO2=84, systolicBP=110, needsVasopressors=False)
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    # spO2 84 + mechVent => "Severe hypoxemic respiratory failure" moderate indication,
    # no strong indication, no relative contra -> conditional, config VV consideration
    assert r["recommendedConfig"] == "VA-ECMO (with VV consideration)"


# ---- Prognostic factors ----
def test_prognostic_high_lactate():
    p = pt(lactate=8)
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    assert any(">6): associated with worse outcomes" in s for s in r["keyPrognosticFactors"])


def test_prognostic_low_lactate():
    p = pt(lactate=3)
    cls = classify_pe(p)
    inp = create_default_ecmo_input(p, cls)
    r = assess_ecmo_candidacy(inp)
    assert any("favorable prognostic sign" in s for s in r["keyPrognosticFactors"])


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
