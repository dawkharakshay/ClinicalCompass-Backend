"""Tests for the ACS Clinical Compass port.

The legacy oracle test (old_static_code/server/acs.test.ts) only exercised
persistence (saveAssessment/getHistory/deleteAssessment), not the decision
engine. These fixtures are therefore derived directly from the branches of
assessACS / its helpers in old_static_code/client/src/lib/acsLogic.ts, covering
each major decision path plus contraindication/edge paths.
"""

from __future__ import annotations

from app.recommendations.modules.acs import assess


def _base() -> dict:
    """A minimal low-risk patient with all flags off."""
    return {
        "age": 50,
        "weight": 80,
        "sex": "M",
        "acsType": "NSTEMI",
        "symptomOnsetTime": None,
        "presentationTime": None,
        "priorMI": False,
        "priorPCI": False,
        "priorCABG": False,
        "diabetes": False,
        "hypertension": False,
        "smoker": False,
        "recentCocaineUse": False,
        "systolicBP": 120,
        "heartRate": 80,
        "killipClass": 1,
        "cardiogenicShock": False,
        "troponinLevel": 0,
        "troponinElevated": False,
        "hemoglobin": 14,
        "creatinine": 1.0,
        "stSegmentElevation": False,
        "stSegmentDepression": False,
        "tWaveInversion": False,
        "newLBBB": False,
        "priorStroke": False,
        "priorTIA": False,
        "activeBleed": False,
        "recentSurgery": False,
        "chronicKidneyDisease": False,
        "onOralAnticoagulant": False,
        "femurAccess": False,
        "radialAccess": False,
        "canAccessCathLab": False,
        "fibrinolyticContraindication": False,
    }


# --- classifyACSType -------------------------------------------------------


def test_classify_stemi_via_st_elevation():
    d = _base()
    d["stSegmentElevation"] = True
    assert assess(d)["acsType"] == "STEMI"


def test_classify_stemi_via_new_lbbb():
    d = _base()
    d["newLBBB"] = True
    assert assess(d)["acsType"] == "STEMI"


def test_classify_nstemi_via_troponin():
    d = _base()
    d["troponinElevated"] = True
    assert assess(d)["acsType"] == "NSTEMI"


def test_classify_unstable_angina():
    d = _base()
    assert assess(d)["acsType"] == "UNSTABLE_ANGINA"


# --- STEMI risk is always HIGH ---------------------------------------------


def test_stemi_risk_is_high():
    d = _base()
    d["stSegmentElevation"] = True
    assert assess(d)["riskLevel"] == "HIGH"


# --- calculateNSTERiskLevel ------------------------------------------------


def test_nste_low_risk():
    # troponin not elevated, no risk factors -> score 0 -> LOW
    d = _base()
    assert assess(d)["riskLevel"] == "LOW"


def test_nste_intermediate_risk():
    # troponin elevated (3) -> >=3 -> INTERMEDIATE
    d = _base()
    d["troponinElevated"] = True
    assert assess(d)["riskLevel"] == "INTERMEDIATE"


def test_nste_high_risk():
    # troponin(3) + age>=65(1) + priorMI(1) + killip>=2(2) = 7 -> HIGH
    d = _base()
    d["troponinElevated"] = True
    d["age"] = 70
    d["priorMI"] = True
    d["killipClass"] = 2
    assert assess(d)["riskLevel"] == "HIGH"


def test_nste_bnp_contributes_to_score():
    # troponin(3) + bnp>100(1) = 4 -> INTERMEDIATE; without bnp -> 3 still INT.
    # Use a case where bnp tips from LOW(2) to INTERMEDIATE(3).
    # diabetes(1) + age>=65(1) = 2 -> LOW; add bnp -> 3 -> INTERMEDIATE
    d = _base()
    d["diabetes"] = True
    d["age"] = 66
    d["bNPLevel"] = 150
    assert assess(d)["riskLevel"] == "INTERMEDIATE"


# --- assessBleedingRisk ----------------------------------------------------


def test_bleeding_low():
    d = _base()
    assert assess(d)["bleedingRisk"] == "LOW"


def test_bleeding_moderate_via_age():
    # age 65 -> +1; creatinine 1.6 -> +1 = 2 -> MODERATE
    d = _base()
    d["age"] = 65
    d["creatinine"] = 1.6
    assert assess(d)["bleedingRisk"] == "MODERATE"


def test_bleeding_high():
    # age>=75(2) + creat>2(2) + hgb<10(2) = 6 -> HIGH
    d = _base()
    d["age"] = 80
    d["creatinine"] = 2.5
    d["hemoglobin"] = 9
    assert assess(d)["bleedingRisk"] == "HIGH"


# --- recommendP2Y12Inhibitor ----------------------------------------------


def test_p2y12_clopidogrel_prior_stroke():
    d = _base()
    d["priorStroke"] = True
    assert assess(d)["recommendedP2Y12"] == "CLOPIDOGREL"


def test_p2y12_clopidogrel_low_weight():
    d = _base()
    d["weight"] = 55
    assert assess(d)["recommendedP2Y12"] == "CLOPIDOGREL"


def test_p2y12_clopidogrel_high_bleeding():
    # high bleeding but no individual prasugrel contraindication
    # (age<75, weight ok, no stroke/TIA)
    d = _base()
    d["creatinine"] = 2.5  # +2
    d["hemoglobin"] = 9  # +2
    d["chronicKidneyDisease"] = True  # +1 => 5 HIGH
    d["age"] = 60
    res = assess(d)
    assert res["bleedingRisk"] == "HIGH"
    assert res["recommendedP2Y12"] == "CLOPIDOGREL"


def test_p2y12_prasugrel_stemi():
    # Note: TS recommendP2Y12Inhibitor reads the raw data.acsType input field,
    # not the classified type, so the fixture sets acsType explicitly.
    d = _base()
    d["acsType"] = "STEMI"
    d["stSegmentElevation"] = True
    d["age"] = 50
    d["weight"] = 80
    assert assess(d)["recommendedP2Y12"] == "PRASUGREL"


def test_p2y12_ticagrelor_nstemi():
    d = _base()
    d["troponinElevated"] = True
    assert assess(d)["recommendedP2Y12"] == "TICAGRELOR"


# --- recommendAnticoagulant ------------------------------------------------


def test_anticoagulant_high_bleeding_fondaparinux():
    d = _base()
    d["creatinine"] = 2.5  # <=3.0
    d["hemoglobin"] = 9
    d["chronicKidneyDisease"] = True
    res = assess(d)
    assert res["bleedingRisk"] == "HIGH"
    assert res["recommendedAnticoagulant"] == "FONDAPARINUX"


def test_anticoagulant_high_bleeding_ufh_severe_renal():
    d = _base()
    d["creatinine"] = 3.5  # >3.0
    d["hemoglobin"] = 9  # +2
    d["chronicKidneyDisease"] = True  # +1 ; creat>2 +2 => 5 HIGH
    res = assess(d)
    assert res["bleedingRisk"] == "HIGH"
    assert res["recommendedAnticoagulant"] == "UFH"


def test_anticoagulant_moderate_lmwh():
    d = _base()
    d["age"] = 65  # +1
    d["creatinine"] = 1.6  # +1 => 2 MODERATE, creat not >2
    res = assess(d)
    assert res["bleedingRisk"] == "MODERATE"
    assert res["recommendedAnticoagulant"] == "LMWH"


def test_anticoagulant_moderate_ufh_high_creat():
    d = _base()
    d["age"] = 65  # +1
    d["creatinine"] = 2.5  # +2 => 3 MODERATE, creat>2
    res = assess(d)
    assert res["bleedingRisk"] == "MODERATE"
    assert res["recommendedAnticoagulant"] == "UFH"


def test_anticoagulant_low_bivalirudin_stemi_cathlab():
    # TS recommendAnticoagulant reads the raw data.acsType input field.
    d = _base()
    d["acsType"] = "STEMI"
    d["stSegmentElevation"] = True
    d["canAccessCathLab"] = True
    res = assess(d)
    assert res["bleedingRisk"] == "LOW"
    assert res["recommendedAnticoagulant"] == "BIVALIRUDIN"


def test_anticoagulant_low_ufh_default():
    d = _base()
    res = assess(d)
    assert res["bleedingRisk"] == "LOW"
    assert res["recommendedAnticoagulant"] == "UFH"


# --- STEMI reperfusion + time-to-reperfusion -------------------------------


def test_stemi_ppci_within_window():
    # onset->presentation 20 min + 90 door-to-balloon = 110 <= 120 -> PPCI
    d = _base()
    d["stSegmentElevation"] = True
    d["canAccessCathLab"] = True
    d["symptomOnsetTime"] = "2026-06-10T10:00:00"
    d["presentationTime"] = "2026-06-10T10:20:00"
    res = assess(d)
    assert res["recommendedStrategy"] == "PPCI"
    assert res["timeToReperfusion"] == 90


def test_stemi_fibrinolytic_when_delayed():
    # onset->presentation 60 min + 90 = 150 > 120, no contraindication -> FIBRINOLYTIC
    d = _base()
    d["stSegmentElevation"] = True
    d["canAccessCathLab"] = True
    d["symptomOnsetTime"] = "2026-06-10T10:00:00"
    d["presentationTime"] = "2026-06-10T11:00:00"
    res = assess(d)
    assert res["recommendedStrategy"] == "FIBRINOLYTIC"
    assert res["timeToReperfusion"] == 30


def test_stemi_fibrinolytic_no_cathlab():
    d = _base()
    d["stSegmentElevation"] = True
    d["canAccessCathLab"] = False
    res = assess(d)
    assert res["recommendedStrategy"] == "FIBRINOLYTIC"
    assert res["timeToReperfusion"] == 30


def test_stemi_ppci_when_fibrinolytic_contraindicated():
    # no cath lab access, fibrinolytic contraindicated -> PPCI (referral)
    d = _base()
    d["stSegmentElevation"] = True
    d["canAccessCathLab"] = False
    d["fibrinolyticContraindication"] = True
    res = assess(d)
    assert res["recommendedStrategy"] == "PPCI"
    assert res["timeToReperfusion"] == 90


# --- NSTE invasive strategy + time ----------------------------------------


def test_nste_routine_invasive_high_risk():
    d = _base()
    d["troponinElevated"] = True
    d["age"] = 70
    d["priorMI"] = True
    d["killipClass"] = 2
    res = assess(d)
    assert res["riskLevel"] == "HIGH"
    assert res["recommendedStrategy"] == "ROUTINE_INVASIVE"
    assert res["timeToReperfusion"] == 240


def test_nste_selective_invasive_low_risk():
    d = _base()
    res = assess(d)
    assert res["riskLevel"] == "LOW"
    assert res["recommendedStrategy"] == "SELECTIVE_INVASIVE"
    assert res["timeToReperfusion"] == 0


# --- vascular access -------------------------------------------------------


def test_vascular_radial_preferred():
    d = _base()
    d["radialAccess"] = True
    assert (
        "Radial approach preferred (reduces bleeding and vascular complications)"
        in assess(d)["recommendations"]
    )


def test_vascular_femoral_acceptable():
    d = _base()
    d["femurAccess"] = True
    assert "Femoral approach acceptable if radial unavailable" in assess(d)["recommendations"]


def test_vascular_default_radial_recommended():
    d = _base()
    assert "Radial approach strongly recommended for ACS" in assess(d)["recommendations"]


# --- special considerations / contraindications ----------------------------


def test_cardiogenic_shock_special_considerations():
    d = _base()
    d["cardiogenicShock"] = True
    sc = assess(d)["specialConsiderations"]
    assert (
        "Cardiogenic shock present: emergency revascularization of culprit vessel indicated"
        in sc
    )
    assert (
        "Consider mechanical circulatory support (microaxial flow pump) in selected cases" in sc
    )


def test_anemia_special_consideration_formats_integer():
    d = _base()
    d["hemoglobin"] = 9
    sc = assess(d)["specialConsiderations"]
    assert "Hemoglobin 9 g/dL: consider transfusion to maintain Hgb ≥10 g/dL" in sc


def test_high_bleeding_adds_ppi_and_monotherapy():
    d = _base()
    d["creatinine"] = 2.5
    d["hemoglobin"] = 9
    d["chronicKidneyDisease"] = True
    res = assess(d)
    assert res["bleedingRisk"] == "HIGH"
    assert "Proton pump inhibitor for GI bleeding prevention" in res["recommendations"]
    assert (
        "High bleeding risk: consider ticagrelor monotherapy ≥1 month post-PCI"
        in res["specialConsiderations"]
    )


def test_fibrinolytic_contraindication_stemi():
    d = _base()
    d["stSegmentElevation"] = True
    d["fibrinolyticContraindication"] = True
    assert "Fibrinolytic contraindication present" in assess(d)["contraindications"]


def test_fibrinolytic_contraindication_not_listed_for_nstemi():
    d = _base()
    d["troponinElevated"] = True
    d["fibrinolyticContraindication"] = True
    assert "Fibrinolytic contraindication present" not in assess(d)["contraindications"]


def test_prior_stroke_contraindication():
    d = _base()
    d["priorTIA"] = True
    assert "Prior stroke/TIA: prasugrel contraindicated" in assess(d)["contraindications"]


# --- standard recommendations always present -------------------------------


def test_standard_recommendations_present():
    d = _base()
    recs = assess(d)["recommendations"]
    assert "Dual antiplatelet therapy (aspirin + P2Y12 inhibitor) for ≥12 months" in recs
    assert (
        "High-intensity statin therapy (atorvastatin 80 mg or rosuvastatin 40 mg daily)" in recs
    )


def test_result_shape():
    d = _base()
    res = assess(d)
    assert set(res.keys()) == {
        "acsType",
        "riskLevel",
        "recommendedStrategy",
        "recommendedP2Y12",
        "recommendedAnticoagulant",
        "bleedingRisk",
        "timeToReperfusion",
        "recommendations",
        "contraindications",
        "specialConsiderations",
    }
