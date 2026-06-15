"""Tests for PE Classification — ported 1:1 from
old_static_code/server/pe.classification.test.ts.
"""

from __future__ import annotations

import pytest

from app.recommendations.shared.pe_classification import (
    assess_contraindications,
    calculate_bova,
    calculate_spesi,
    classify_pe,
    patient_data,
)

# Base patient — healthy normotensive, sPESI = 0
BASE = {
    "name": "Test Patient",
    "age": 45,
    "weight": 70,
    "heartRate": 80,
    "systolicBP": 120,
    "diastolicBP": 80,
    "respiratoryRate": 16,
    "spO2": 98,
    "temperature": 37.0,
    "symptomatic": True,
    "subsegmental": False,
    "rvDilation": False,
    "rvDysfunction": False,
    "tapse": 2.0,
    "clotBurden": "low",
    "troponin": 0.01,
    "troponinElevated": False,
    "bnp": 50,
    "bnpElevated": False,
    "lactate": 1.0,
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


def pt(**overrides):
    d = dict(BASE)
    d.update(overrides)
    return patient_data(d)


# ---- Category A ----
def test_classifies_asymptomatic_as_A():
    assert classify_pe(pt(symptomatic=False))["category"] == "A"


def test_category_A_minimal_risk():
    assert classify_pe(pt(symptomatic=False))["riskLevel"] == "minimal"


# ---- Category B ----
def test_subsegmental_is_B1():
    assert classify_pe(pt(subsegmental=True))["category"] == "B1"


def test_non_subsegmental_low_severity_is_B2():
    assert classify_pe(pt())["category"] == "B2"


def test_B2_anticoagulation_treatment():
    assert "anticoagul" in classify_pe(pt())["treatment"].lower()


def test_B2_hemodynamically_stable():
    assert classify_pe(pt())["hemodynamicStatus"] == "stable"


# ---- Category C ----
def test_spesi_ge_1_is_C():
    assert classify_pe(pt(cancer=True))["category"].startswith("C")


def test_elevated_hr_is_C():
    assert classify_pe(pt(heartRate=115))["category"].startswith("C")


# ---- Category D ----
def test_rv_and_biomarkers_is_C_or_D():
    r = classify_pe(pt(cancer=True, rvDilation=True, rvDysfunction=True,
                        troponinElevated=True, bnpElevated=True, tapse=1.4))
    assert r["category"][0] in ("C", "D")


def test_transient_hypotension_is_D():
    r = classify_pe(pt(cancer=True, rvDilation=True, rvDysfunction=True,
                        troponinElevated=True, transientHypotension=True))
    assert r["category"].startswith("D")


# ---- Category E ----
def test_persistent_hypotension_with_shock_is_E():
    r = classify_pe(pt(persistentHypotension=True, systolicBP=80, rvDilation=True,
                        rvDysfunction=True, troponinElevated=True, lactate=3.5))
    assert r["category"].startswith("E")


def test_cardiac_arrest_is_E2():
    r = classify_pe(pt(cardiacArrest=True, refractoryShock=True, persistentHypotension=True,
                        systolicBP=60, rvDilation=True, rvDysfunction=True))
    assert r["category"] == "E2"


def test_category_E_unstable():
    r = classify_pe(pt(cardiacArrest=True, refractoryShock=True, systolicBP=60))
    assert r["hemodynamicStatus"] == "unstable"


# ---- sPESI ----
def test_spesi_zero_low_risk():
    assert calculate_spesi(pt())["score"] == 0


def test_spesi_age_gt_80():
    r = calculate_spesi(pt(age=85))
    assert r["score"] >= 1
    assert "Age > 80" in r["details"]


def test_spesi_cancer():
    r = calculate_spesi(pt(cancer=True))
    assert r["score"] >= 1
    assert "Active cancer" in r["details"]


def test_spesi_hr_ge_110():
    r = calculate_spesi(pt(heartRate=115))
    assert r["score"] >= 1
    assert "HR ≥ 110" in r["details"]


def test_spesi_spo2_lt_90():
    r = calculate_spesi(pt(spO2=88))
    assert r["score"] >= 1
    assert "SpO2 < 90%" in r["details"]


def test_spesi_sbp_lt_100():
    r = calculate_spesi(pt(systolicBP=95))
    assert r["score"] >= 1
    assert "SBP < 100 mmHg" in r["details"]


def test_spesi_details_is_list():
    assert isinstance(calculate_spesi(pt())["details"], list)


# ---- BOVA ----
def test_bova_stage_I_low_risk():
    r = calculate_bova(pt())
    assert r["score"] <= 2
    assert "Stage I" in r["stage"]


def test_bova_increases_with_troponin():
    assert calculate_bova(pt(troponinElevated=True))["score"] > 0


def test_bova_increases_with_rv_dysfunction():
    assert calculate_bova(pt(rvDysfunction=True))["score"] > 0


def test_bova_stage_III_high():
    r = calculate_bova(pt(heartRate=115, systolicBP=85, rvDysfunction=True, troponinElevated=True))
    assert r["score"] >= 5
    assert "Stage III" in r["stage"]


# ---- Contraindications ----
def test_contraindication_result_object():
    r = assess_contraindications(pt())
    assert r is not None
    assert "systemicThrombolysis" in r
    assert "cdt" in r
    assert "anticoagulation" in r


def test_healthy_eligible_anticoagulation():
    assert assess_contraindications(pt())["anticoagulation"]["eligible"] is True


def test_active_bleeding_absolute_thrombolysis():
    r = assess_contraindications(pt(activeBleeding=True))
    assert len(r["systemicThrombolysis"]["absolute"]) > 0
    assert r["systemicThrombolysis"]["eligible"] is False


def test_recent_stroke_absolute_thrombolysis():
    r = assess_contraindications(pt(recentStroke=True))
    assert len(r["systemicThrombolysis"]["absolute"]) > 0
    assert r["systemicThrombolysis"]["eligible"] is False


def test_intracranial_neoplasm_absolute_thrombolysis():
    r = assess_contraindications(pt(intracranialNeoplasm=True))
    assert len(r["systemicThrombolysis"]["absolute"]) > 0
    assert r["systemicThrombolysis"]["eligible"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
