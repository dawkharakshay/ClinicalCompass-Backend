"""Thyroid Nodule engine — fixtures derived directly from thyroidNoduleLogic.ts
branches. No TS oracle test exists for this module; cases cover each major
decision path plus edge/contraindication paths."""

from app.recommendations.modules.thyroidnodule import (
    assess,
    calculate_tirads,
    get_biopsy_threshold,
)


def _base() -> dict:
    # A benign-looking, low-risk nodule with no FNA performed.
    return {
        "noduleSize": "1.0",
        "composition": "cystic",
        "echogenicity": "anechoic",
        "shape": "wider_than_tall",
        "margin": "smooth",
        "echogenicFoci": "none",
        "bethesdaCategory": "not_done",
        "age": "45",
        "sex": "female",
        "priorHeadNeckRT": False,
        "familyHistoryThyroidCancer": False,
        "familyHistoryMEN2": False,
        "priorThyroidCancer": False,
        "dysphagia": False,
        "dysphonia": False,
        "compressiveSymptoms": False,
        "tshLevel": "2.0",
        "suspiciousLymphadenopathy": False,
        "multinodularGoiter": False,
        "dominantNodule": False,
    }


# ─── TI-RADS scoring ─────────────────────────────────────────────────────────

def test_tirads_tr5_high_score():
    r = calculate_tirads({
        "composition": "solid",          # +2
        "echogenicity": "markedly_hypoechoic",  # +3
        "shape": "taller_than_wide",     # +3
        "margin": "irregular",           # +2
        "echogenicFoci": "punctate_echogenic_foci",  # +3
    })
    assert r["score"] == 13
    assert r["category"] == "TR5"


def test_tirads_tr1_all_zero():
    r = calculate_tirads({
        "composition": "cystic",
        "echogenicity": "anechoic",
        "shape": "wider_than_tall",
        "margin": "smooth",
        "echogenicFoci": "none",
    })
    assert r["score"] == 0
    assert r["category"] == "TR1"


def test_tirads_tr3_score_three():
    # mixed(+1) + isoechoic(+1) + lobulated(+2) = wait that's 4 -> TR4.
    # Use mixed(+1) + hypoechoic(+2) = 3 -> TR3
    r = calculate_tirads({
        "composition": "mixed",
        "echogenicity": "hypoechoic",
        "shape": "wider_than_tall",
        "margin": "smooth",
        "echogenicFoci": "none",
    })
    assert r["score"] == 3
    assert r["category"] == "TR3"


def test_biopsy_threshold_table():
    assert get_biopsy_threshold("TR5")["size"] == 1.0
    assert get_biopsy_threshold("TR4")["size"] == 1.5
    assert get_biopsy_threshold("TR3")["size"] == 2.5
    assert get_biopsy_threshold("TR2")["size"] == 0


# ─── Bethesda-based branches ─────────────────────────────────────────────────

def test_compressive_symptoms_surgery():
    r = assess({**_base(), "compressiveSymptoms": True})
    assert r["decision"] == "surgery_recommended"
    assert r["decisionLabel"] == "Surgery Recommended"
    assert "Compressive symptoms" in r["surgicalRationale"]
    assert r["surveillanceInterval"] is None


def test_bethesda_vi_malignant():
    r = assess({**_base(), "bethesdaCategory": "VI"})
    assert r["decision"] == "surgery_recommended"
    assert r["decisionLabel"] == "Surgery Recommended (Bethesda VI — Malignant)"
    assert r["malignancyRisk"] == "97-99% (Bethesda VI)"
    # noduleSize 1.0 <= 1 and no high-risk -> lobectomy/active surveillance
    assert "active surveillance is an option" in r["surgicalExtent"]
    assert any("active surveillance is an ATA 2023 option" in w for w in r["keyWarnings"])


def test_bethesda_vi_with_high_risk_is_urgent_total():
    # Bethesda VI + high-risk clinical -> urgent branch fires first.
    r = assess({**_base(), "bethesdaCategory": "VI", "priorThyroidCancer": True})
    assert r["decision"] == "surgery_recommended"
    assert r["decisionLabel"] == "Surgery Recommended"
    assert r["surgicalExtent"].startswith("Total thyroidectomy")
    assert "Bethesda VI with high-risk features" in r["surgicalRationale"]
    assert r["biopsyIndicated"] is False  # bethesda != not_done


def test_bethesda_v_suspicious():
    r = assess({**_base(), "bethesdaCategory": "V"})
    assert r["decision"] == "surgery_recommended"
    assert r["malignancyRisk"] == "60-75% (Bethesda V)"


def test_bethesda_iv_molecular():
    r = assess({**_base(), "bethesdaCategory": "IV", "noduleSize": "5"})
    assert r["decision"] == "molecular_testing"
    assert r["malignancyRisk"] == "25-40% (Bethesda IV)"
    assert "size >4 cm" in r["bethesdaRecommendation"]
    assert any("follicular adenoma" in w for w in r["keyWarnings"])


def test_bethesda_iii_molecular():
    r = assess({**_base(), "bethesdaCategory": "III"})
    assert r["decision"] == "molecular_testing"
    assert r["decisionLabel"] == "Molecular Testing or Repeat FNA (Bethesda III)"
    assert r["evidenceLevel"] == "Moderate"


def test_bethesda_iii_high_risk_appended():
    r = assess({**_base(), "bethesdaCategory": "III", "age": "70"})
    assert "HIGH RISK" in r["bethesdaRecommendation"]


def test_bethesda_ii_benign_surveillance():
    r = assess({**_base(), "bethesdaCategory": "II"})
    assert r["decision"] == "repeat_ultrasound"
    assert r["malignancyRisk"] == "0-3% (Bethesda II)"
    assert any("false-negative rate" in w for w in r["keyWarnings"])


# ─── TI-RADS-driven (no FNA) branches ────────────────────────────────────────

def test_tr1_no_biopsy_observe():
    r = assess(_base())  # cystic/anechoic -> TR1
    assert r["calculatedTIRADS"] == "TR1"
    assert r["decision"] == "no_biopsy_observe"
    assert r["surveillanceInterval"] == "No follow-up needed"


def test_tr5_biopsy_recommended_at_threshold():
    r = assess({
        **_base(),
        "noduleSize": "1.5",
        "composition": "solid",
        "echogenicity": "markedly_hypoechoic",
        "shape": "taller_than_wide",
        "margin": "irregular",
        "echogenicFoci": "punctate_echogenic_foci",
    })
    assert r["calculatedTIRADS"] == "TR5"
    assert r["decision"] == "biopsy_recommended"
    assert r["biopsyIndicated"] is True
    assert "size 1.5 cm" in r["decisionLabel"]
    assert "Ultrasound-guided FNA biopsy" in r["nextSteps"]


def test_tr5_below_threshold_biopsy_optional():
    # TR5 threshold 1.0; 0.6*1.0=0.6 <= size < 1.0 -> optional
    r = assess({
        **_base(),
        "noduleSize": "0.7",
        "composition": "solid",
        "echogenicity": "markedly_hypoechoic",
        "shape": "taller_than_wide",
        "margin": "irregular",
        "echogenicFoci": "punctate_echogenic_foci",
    })
    assert r["calculatedTIRADS"] == "TR5"
    assert r["decision"] == "biopsy_optional"
    assert r["biopsyIndicated"] is True
    assert "below threshold" in r["decisionLabel"]
    assert r["surveillanceInterval"] == "Repeat ultrasound in 6-12 months"


def test_tr4_far_below_threshold_surveillance():
    # TR4 threshold 1.5; size 0.5 < 0.6*1.5=0.9 -> repeat_ultrasound
    r = assess({
        **_base(),
        "noduleSize": "0.5",
        "composition": "solid",      # +2
        "echogenicity": "hypoechoic",  # +2
        "shape": "wider_than_tall",
        "margin": "smooth",
        "echogenicFoci": "none",
    })
    assert r["calculatedTIRADS"] == "TR4"
    assert r["decision"] == "repeat_ultrasound"
    assert r["biopsyIndicated"] is False
    assert r["surveillanceInterval"] == "Repeat ultrasound in 1 year"


def test_high_risk_clinical_forces_biopsy():
    # TR4 below threshold, but suspicious lymphadenopathy -> biopsy_recommended
    r = assess({
        **_base(),
        "noduleSize": "0.5",
        "composition": "solid",
        "echogenicity": "hypoechoic",
        "suspiciousLymphadenopathy": True,
    })
    assert r["calculatedTIRADS"] == "TR4"
    assert r["decision"] == "biopsy_recommended"
    assert any("lymphadenopathy" in w for w in r["keyWarnings"])


# ─── Warnings & TSH ──────────────────────────────────────────────────────────

def test_suppressed_tsh_warning_and_scan_step():
    r = assess({
        **_base(),
        "noduleSize": "1.5",
        "composition": "solid",
        "echogenicity": "markedly_hypoechoic",
        "shape": "taller_than_wide",
        "margin": "irregular",
        "echogenicFoci": "punctate_echogenic_foci",
        "tshLevel": "0.2",
    })
    assert any("Suppressed TSH" in w for w in r["keyWarnings"])
    assert any("Thyroid scan (I-123) before FNA" in s for s in r["nextSteps"])


def test_elevated_tsh_warning():
    r = assess({**_base(), "tshLevel": "5.0"})
    assert any("Elevated TSH" in w for w in r["keyWarnings"])


def test_tirads_category_override_passed_through():
    # When tiRadsCategory provided, calculateTIRADS is skipped.
    r = assess({**_base(), "tiRadsCategory": "TR4", "tiRadsScore": "5",
                "bethesdaCategory": "not_done", "noduleSize": "2.0"})
    assert r["calculatedTIRADS"] == "TR4"
    assert r["tiRadsScore"] == "5"
    assert r["decision"] == "biopsy_recommended"
