"""Tests for the Central Sleep Apnea Compass port.

No legacy *.test.ts exists; fixtures derive from the inline evaluate() branches
in old_static_code/client/src/pages/CentralSleepApneaCompass.tsx.
"""

from app.recommendations.modules.centralsleepapnea import assess


def test_csa_diagnosis_true_and_severity_severe():
    r = assess({"ahi": "35", "cai": "10", "cai_percent": "60"})
    assert r["csaDiagnosis"] is True
    assert r["severity"] == "severe"
    assert r["appealStrength"] == "strong"
    assert r["authRequired"] is True
    assert "CSA diagnosis criteria met: CAI ≥5 with >50% central events" in r["keyFindings"]
    assert "AHI: 35 events/hour — severe sleep apnea" in r["keyFindings"]
    assert (
        "Central Apnea Index (CAI): 10 events/hour (60% of total events)"
        in r["keyFindings"]
    )


def test_csa_diagnosis_false_low_cai():
    r = assess({"ahi": "20", "cai": "3", "cai_percent": "60"})
    assert r["csaDiagnosis"] is False
    assert r["severity"] == "moderate"
    assert r["appealStrength"] == "moderate"


def test_csa_diagnosis_false_low_percent():
    r = assess({"ahi": "10", "cai": "8", "cai_percent": "40"})
    assert r["csaDiagnosis"] is False
    assert r["severity"] == "mild"


def test_empty_inputs_default_branch():
    r = assess({})
    assert r["csaDiagnosis"] is False
    assert r["severity"] == "mild"
    assert r["recommendations"] == [
        "CPAP: First-line trial for most CSA etiologies — AASM 2025",
        "ASV: Conditionally recommended if CPAP inadequate (except HFrEF)",
    ]
    assert r["keyFindings"] == []
    assert r["contraindications"] == []


def test_hfref_contraindication_via_lvef_reduced():
    r = assess({"etiology": "cheyneStokes", "lvef_reduced": True, "ef_percent": "50"})
    assert r["contraindications"] == [
        "ASV is CONTRAINDICATED in HFrEF (EF <45%) with predominantly CSA — AASM 2025 / SERVE-HF trial: increased cardiovascular mortality"
    ]
    assert (
        "Optimize heart failure therapy (ACE-I/ARB, beta-blocker, diuretics, SGLT2 inhibitor)"
        in r["recommendations"]
    )
    assert "⚠️ Reduced EF — ASV CONTRAINDICATED (SERVE-HF / AASM 2025)" in r["keyFindings"]


def test_hfref_contraindication_via_low_ef():
    r = assess({"comorbid_hf": True, "ef_percent": "30"})
    assert len(r["contraindications"]) == 1
    assert "Supplemental oxygen: Conditionally recommended for CSA-CSR in HFrEF" in r["recommendations"]


def test_hfpef_no_contraindication():
    r = assess({"etiology": "cheyneStokes", "ef_percent": "50"})
    assert r["contraindications"] == []
    assert r["recommendations"] == [
        "ASV: Conditionally recommended for CSA-CSR in HFpEF (EF ≥45%) — AASM 2025",
        "CPAP: Conditionally recommended as first-line for CSA-CSR",
    ]


def test_opioid_branch_with_mme():
    r = assess({"etiology": "opioid", "opioid_use": True, "opioid_mme": "250"})
    assert (
        "BPAP with backup rate: Conditionally recommended for opioid-induced CSA — AASM 2025"
        in r["recommendations"]
    )
    assert (
        "Opioid dose: 250 MME/day — CSA risk increases significantly above 200 MME/day"
        in r["notes"]
    )
    assert "Opioid use: 250 MME/day — opioid-induced CSA etiology" in r["keyFindings"]


def test_opioid_branch_missing_mme():
    r = assess({"opioid_use": True})
    assert (
        "Opioid dose: ? MME/day — CSA risk increases significantly above 200 MME/day"
        in r["notes"]
    )
    assert (
        "Opioid use: dose not specified MME/day — opioid-induced CSA etiology"
        in r["keyFindings"]
    )


def test_treatment_emergent_branch():
    r = assess({"etiology": "treatmentEmergent"})
    assert r["recommendations"] == [
        "Continue CPAP — treatment-emergent CSA often resolves within 1–3 months",
        "If persistent ≥3 months: switch to ASV (Conditionally recommended — AASM 2025)",
        "If ASV not tolerated: BPAP with backup rate",
    ]


def test_idiopathic_branch():
    r = assess({"etiology": "idiopathic"})
    assert r["recommendations"] == [
        "CPAP: Suggested as initial therapy for idiopathic CSA — AASM 2025",
        "ASV: Conditionally recommended if CPAP inadequate",
        "Acetazolamide 250–500 mg BID: Conditionally recommended for idiopathic CSA",
    ]


def test_obesity_note_via_bmi():
    r = assess({"etiology": "idiopathic", "bmi": "32"})
    assert any("GLP-1/GIP Agonist" in n for n in r["notes"])


def test_obesity_note_via_flag():
    r = assess({"etiology": "idiopathic", "comorbid_obesity": True})
    assert any("GLP-1/GIP Agonist" in n for n in r["notes"])


def test_no_obesity_note_when_below_threshold():
    r = assess({"etiology": "idiopathic", "bmi": "25"})
    assert r["notes"] == []
