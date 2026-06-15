"""Liver Tumor engine — fixtures derived directly from liverTumorLogic.ts branches."""

from app.recommendations.modules.livertumor import (
    assess,
    classify_bclc,
    is_resection_candidate,
    is_tace_candidate,
)


def _base() -> dict:
    """A solitary 1.5 cm HCC, Child-Pugh A5, ECOG 0, no invasion — BCLC 0."""
    return {
        "tumorType": "hcc",
        "tumorCount": "1",
        "maxTumorSize": "1.5",
        "vascularInvasion": "none",
        "extrahepatic": False,
        "childPugh": "A5",
        "albiGrade": "1",
        "portalHTN": "none",
        "ecogPS": "0",
        "age": "60",
        "afpLevel": "10",
        "futureLiverRemnant": "0",
        "priorLiverResection": False,
        "priorAblation": False,
        "priorTACE": False,
        "transplantEligible": False,
        "milanCriteria": False,
        "subcapsular": False,
        "periHilar": False,
        "adjacentVessel": False,
        "taceSuitability": "suitable",
    }


# ─── classifyBCLC ────────────────────────────────────────────────────────────


def test_bclc_d_child_pugh_c():
    assert classify_bclc({**_base(), "childPugh": "C10"}) == "D"


def test_bclc_d_ecog_3():
    assert classify_bclc({**_base(), "ecogPS": "3"}) == "D"


def test_bclc_c_macro_main():
    assert classify_bclc({**_base(), "vascularInvasion": "macro_main"}) == "C"


def test_bclc_c_extrahepatic():
    assert classify_bclc({**_base(), "extrahepatic": True}) == "C"


def test_bclc_c_ecog_2():
    assert classify_bclc({**_base(), "ecogPS": "2"}) == "C"


def test_bclc_0_solitary_small():
    assert classify_bclc(_base()) == "0"


def test_bclc_a_single_4cm():
    assert classify_bclc({**_base(), "maxTumorSize": "4"}) == "A"


def test_bclc_a_three_nodules():
    assert classify_bclc({**_base(), "tumorCount": "3", "maxTumorSize": "2.5"}) == "A"


def test_bclc_b_multinodular():
    # 4 nodules, 4 cm -> not A, intermediate -> B
    assert classify_bclc({**_base(), "tumorCount": "4", "maxTumorSize": "4"}) == "B"


def test_bclc_b_single_large():
    # single 7 cm -> not A (>5), tumorCount==1 & >5 -> B
    assert classify_bclc({**_base(), "maxTumorSize": "7"}) == "B"


# ─── candidate helpers ───────────────────────────────────────────────────────


def test_resection_blocked_by_low_flr():
    assert is_resection_candidate({**_base(), "futureLiverRemnant": "25"}) is False


def test_resection_ok_flr_zero_means_not_calculated():
    assert is_resection_candidate({**_base(), "futureLiverRemnant": "0"}) is True


def test_resection_blocked_severe_phtn_child_b():
    inp = {**_base(), "childPugh": "B7", "portalHTN": "severe"}
    assert is_resection_candidate(inp) is False


def test_tace_blocked_when_unsuitable():
    assert is_tace_candidate({**_base(), "taceSuitability": "unsuitable_infiltrative"}) is False


# ─── assess: end-stage ───────────────────────────────────────────────────────


def test_assess_d():
    r = assess({**_base(), "childPugh": "C11"})
    assert r["bclcStage"] == "D"
    assert r["primaryModality"] == "best_supportive_care"
    assert r["evidenceLevel"] == "1A"
    assert any("not recommended" in w for w in r["keyWarnings"])
    assert "transplantBridge" not in r


# ─── assess: advanced ────────────────────────────────────────────────────────


def test_assess_c_macro_branch_offers_sbrt():
    r = assess({**_base(), "vascularInvasion": "macro_branch"})
    assert r["bclcStage"] == "C"
    assert r["primaryModality"] == "systemic_first_line"
    assert r["alternativeModalities"] == ["sbrt"]
    assert "HIMALAYA" in r["systemicRegimen"]
    # SBRT-caveat warning present; empty strings filtered out
    assert all(w for w in r["keyWarnings"])
    assert any("SBRT may be considered" in w for w in r["keyWarnings"])


def test_assess_c_extrahepatic_no_sbrt():
    r = assess({**_base(), "extrahepatic": True})
    assert r["bclcStage"] == "C"
    assert r["alternativeModalities"] == []
    assert "Lenvatinib or Sorafenib" in r["systemicRegimen"]


# ─── assess: intermediate ────────────────────────────────────────────────────


def test_assess_b_tace_candidate():
    r = assess({**_base(), "tumorCount": "4", "maxTumorSize": "4"})
    assert r["bclcStage"] == "B"
    assert r["primaryModality"] == "tace"
    assert r["alternativeModalities"] == ["tare_y90", "sbrt"]


def test_assess_b_tace_unsuitable_falls_to_tare():
    r = assess(
        {
            **_base(),
            "tumorCount": "4",
            "maxTumorSize": "4",
            "taceSuitability": "unsuitable_liver_function",
        }
    )
    assert r["bclcStage"] == "B"
    assert r["primaryModality"] == "tare_y90"
    assert r["alternativeModalities"] == ["sbrt", "systemic_first_line"]
    assert any("TACE unsuitable" in w for w in r["keyWarnings"])


def test_assess_b_transplant_bridge():
    r = assess(
        {
            **_base(),
            "tumorCount": "4",
            "maxTumorSize": "4",
            "transplantEligible": True,
            "milanCriteria": True,
        }
    )
    assert r["transplantBridge"].startswith("TACE or TARE as bridge")


# ─── assess: very early (BCLC 0 / ≤2 cm) ─────────────────────────────────────


def test_assess_very_early_prefers_resection():
    r = assess(_base())
    assert r["bclcStage"] == "0"
    assert r["primaryModality"] == "resection"
    assert r["alternativeModalities"] == ["ablation_rfa", "transplant"]
    assert "transplantBridge" not in r


def test_assess_very_early_adjacent_vessel_drops_to_ablation():
    r = assess({**_base(), "adjacentVessel": True})
    assert r["bclcStage"] == "0"
    # prefer_resection blocked by adjacentVessel; ablation candidate -> ablation_rfa
    assert r["primaryModality"] == "ablation_rfa"
    assert r["alternativeModalities"] == ["resection", "transplant"]
    assert any("heat-sink" in w for w in r["keyWarnings"])


def test_assess_very_early_transplant_bridge():
    r = assess({**_base(), "transplantEligible": True})
    assert r["transplantBridge"].startswith("Ablation as bridge")


# ─── assess: BCLC A (>2 cm) ──────────────────────────────────────────────────


def test_assess_a_single_prefers_resection():
    r = assess({**_base(), "maxTumorSize": "4"})
    assert r["bclcStage"] == "A"
    assert r["primaryModality"] == "resection"
    assert r["alternativeModalities"] == ["ablation_rfa", "transplant", "sbrt"]
    assert any("Adjuvant therapy discussion" in s for s in r["nextSteps"])


def test_assess_a_three_nodules_ablation():
    # tumorCount 3 -> prefer_resection False (needs count==1); size 2.5 <=3 & ablation candidate
    r = assess({**_base(), "tumorCount": "3", "maxTumorSize": "2.5"})
    assert r["bclcStage"] == "A"
    assert r["primaryModality"] == "ablation_rfa"
    assert r["alternativeModalities"] == ["resection", "transplant", "sbrt"]


def test_assess_a_non_resection_non_ablation_to_tace():
    # 3 nodules at 4 cm: BCLC A? count<=3 & size<=3 fails (4>3); single&<=5 fails (count 3).
    # That would be B. Instead use count 2, size 4: not A by either rule -> need A.
    # Use count 1, size 4 but block resection via FLR and ablation via size>5? size>5 -> B.
    # Force: count 1 size 4, resection blocked (FLR 20 -> not candidate), ablation candidate
    # but size 4 >3 so ablation_rfa branch needs <=3 -> fails -> transplant if eligible else tace.
    r = assess(
        {
            **_base(),
            "maxTumorSize": "4",
            "futureLiverRemnant": "20",
            "transplantEligible": False,
            "milanCriteria": False,
        }
    )
    assert r["bclcStage"] == "A"
    assert r["primaryModality"] == "tace"


def test_assess_a_transplant_when_eligible_within_milan():
    r = assess(
        {
            **_base(),
            "maxTumorSize": "4",
            "futureLiverRemnant": "20",
            "transplantEligible": True,
            "milanCriteria": True,
        }
    )
    assert r["bclcStage"] == "A"
    assert r["primaryModality"] == "transplant"
    assert r["transplantBridge"] == "TACE or ablation as bridge to transplant"


# ─── warnings ────────────────────────────────────────────────────────────────


def test_afp_warnings_both_thresholds():
    r = assess({**_base(), "afpLevel": "1500"})
    joined = " ".join(r["keyWarnings"])
    assert "AFP >1,000" in joined
    assert "AFP >400" in joined
