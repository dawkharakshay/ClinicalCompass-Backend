"""MASLD / MASH engine — oracle cases ported 1:1 from
old_static_code/server/gi-modules.test.ts (describe assessMASLD), plus
branch-coverage fixtures derived from masldLogic.ts.
"""

import re

from app.recommendations.modules.masld import assess


def _base() -> dict:
    return {
        "hasLiverSteatosis": True,
        "steatosisMethod": "ultrasound",
        "mashStatus": "suspected_mash",
        "estimatedFibrosisStage": "F2",
        "diabetesStatus": "type2_diabetes",
        "hasHypertension": True,
        "hasDyslipidemia": True,
        "hasMetabolicSyndrome": True,
        "hasCardiovascularDisease": False,
        "hasObesity": True,
        "hasCirchosis": False,
        "hasPortalHypertension": False,
        "hasEsophagealVarices": False,
        "hasAscites": False,
        "hasHepaticEncephalopathy": False,
        "hasHCC": False,
        "bmi": 34,
        "fib4Score": 1.8,
        "isOnStatin": False,
    }


# ─── Oracle cases (gi-modules.test.ts) ──────────────────────────────────────


def test_resmetirom_for_biopsy_confirmed_mash_f2_f3():
    r = assess({**_base(), "mashStatus": "biopsy_confirmed_mash", "estimatedFibrosisStage": "F2"})
    assert r["primaryRecommendation"]
    assert r["pharmacotherapy"]
    assert re.match(r"^[ABC]$", r["evidenceLevel"])


def test_glp1_for_masld_obesity_t2dm():
    r = assess(_base())
    assert r["primaryRecommendation"]
    assert r["pharmacotherapy"]


def test_flags_cirrhosis_for_advanced_management():
    r = assess(
        {
            **_base(),
            "hasCirchosis": True,
            "hasAscites": True,
            "estimatedFibrosisStage": "F4_cirrhosis",
        }
    )
    assert re.search(
        r"cirrhosis|HCC|transplant|decompensated", r["primaryRecommendation"], re.IGNORECASE
    )


def test_fib4_reassessment_low_risk():
    r = assess(
        {
            **_base(),
            "mashStatus": "no_mash",
            "estimatedFibrosisStage": "F0",
            "fib4Score": 0.8,
            "bmi": 27,
        }
    )
    assert r["primaryRecommendation"]
    assert r["fibrosisAssessment"]


def test_returns_references():
    r = assess(_base())
    assert len(r["references"]) > 0


# ─── Branch-coverage fixtures (masldLogic.ts) ───────────────────────────────


def test_fib4_intermediate_drives_pharmacotherapy_and_steps():
    # suspected_mash + fib4 1.3-2.67 => intermediate => candidate via second clause
    r = assess(_base())  # fib4 1.8
    assert "FIB-4 1.80 (1.3–2.67): INTERMEDIATE" in r["fibrosisAssessment"]
    assert "PHARMACOTHERAPY FOR MASH WITH SIGNIFICANT FIBROSIS" in r["pharmacotherapy"]
    assert "Liver biopsy CONSIDER (AGA 2024): " in r["liverBiopsyIndication"]
    assert any("FibroScan" in s for s in r["nextSteps"])


def test_fib4_high_risk_biopsy_indicated_and_urgent_path():
    r = assess({**_base(), "fib4Score": 3.5})
    assert "FIB-4 3.50 (>2.67): HIGH risk" in r["fibrosisAssessment"]
    assert "Liver biopsy INDICATED (AGA 2024): " in r["liverBiopsyIndication"]
    assert r["primaryRecommendation"].startswith("MASH with significant fibrosis")
    assert "Advanced fibrosis (F3) surveillance: " in r["surveillancePlan"]


def test_low_risk_f0_f1_no_routine_pharmacotherapy():
    r = assess(
        {
            **_base(),
            "mashStatus": "no_mash",
            "estimatedFibrosisStage": "F1",
            "fib4Score": 0.9,
        }
    )
    assert "MASLD without significant fibrosis (F0–F1)" in r["pharmacotherapy"]
    assert "Semaglutide (Ozempic" in r["recommendedAgents"][0]
    assert r["primaryRecommendation"].startswith("MASLD without significant fibrosis")
    assert "Liver biopsy NOT routinely indicated" in r["liverBiopsyIndication"]


def test_hcc_urgent_flag_and_primary():
    r = assess({**_base(), "hasHCC": True})
    assert r["primaryRecommendation"].startswith("Hepatocellular carcinoma detected")
    assert any("HEPATOCELLULAR CARCINOMA" in f for f in r["urgentFlags"])


def test_meld_15_transplant_and_urgent():
    r = assess({**_base(), "meldScore": 18})
    assert any("MELD score 18 ≥15" in f for f in r["urgentFlags"])
    assert r["transplantConsideration"].startswith("MELD 18 ≥15")


def test_child_pugh_c_pharmacotherapy_deprioritized():
    r = assess({**_base(), "hasCirchosis": True, "childPughScore": "C"})
    assert "Decompensated cirrhosis (Child-Pugh C)" in r["pharmacotherapy"]


def test_lsm_high_adds_urgent_flag():
    # No fib4 => falls to lsm branch
    d = _base()
    d.pop("fib4Score")
    d["lsm_kPa"] = 15
    d["mashStatus"] = "no_mash"
    d["estimatedFibrosisStage"] = "F3"
    r = assess(d)
    assert "FibroScan LSM 15kPa (≥12kPa): HIGH risk" in r["fibrosisAssessment"]
    assert any("FibroScan LSM ≥12kPa" in f for f in r["urgentFlags"])


def test_no_noninvasive_test_default_pathway():
    d = _base()
    d.pop("fib4Score")
    d["mashStatus"] = "suspected_mash"
    d["estimatedFibrosisStage"] = "F2"
    r = assess(d)
    assert "Noninvasive fibrosis assessment not yet performed." in r["fibrosisAssessment"]
    # F2 still makes patient a pharmacotherapy candidate
    assert "PHARMACOTHERAPY FOR MASH WITH SIGNIFICANT FIBROSIS" in r["pharmacotherapy"]


def test_alcohol_over_20_urgent_flag():
    r = assess({**_base(), "alcoholUseGramsPerDay": 40})
    assert any("Significant alcohol use (40g/day)" in f for f in r["urgentFlags"])


def test_statin_recommended_when_cvd_and_not_on_statin():
    r = assess({**_base(), "hasCardiovascularDisease": True, "isOnStatin": False})
    assert any("High-intensity statin" in a for a in r["recommendedAgents"])
