"""Oracle tests ported 1:1 from old_static_code/server/hematology.test.ts
(Aplastic Anemia Pathway Tool describe block) plus edge paths."""

import re

from app.recommendations.modules.aplasticanemia import assess, classify_aa_severity


def _base():
    return {
        "age": 30,
        "ecogPS": 1,
        "severity": "severe",
        "etiology": "idiopathic",
        "inheritedType": "none",
        "anc": 300,
        "reticulocytes": 15000,
        "platelets": 15,
        "hemoglobin": 7.5,
        "hasPNHClone": False,
        "hasMDSFeatures": False,
        "hasClonalCytogenetics": False,
        "hasSF3B1OrOtherMDSMutation": False,
        "hasTelomereDisease": False,
        "priorIST": False,
        "priorEltrombopag": False,
        "priorHCT": False,
        "donorAvailability": "hla_matched_sibling",
        "patientPreference": "aggressive",
        "priorISTResponse": "na",
    }


def test_saa_young_msd_hct_recommended():
    result = assess(_base())
    assert re.search(r"HCT|transplant|MSD", result["transplantRecommendation"], re.I)


def test_saa_no_donor_hatg_csa_eltro():
    result = assess({**_base(), "donorAvailability": "none"})
    assert re.search(r"hATG|IST|immunosuppression|eltrombopag", result["primaryLabel"], re.I)


def test_vsaa_anc_under_200_very_severe():
    severity = classify_aa_severity(150, 10000, 10)
    assert severity == "very_severe"


def test_nsaa_non_severe_classification():
    severity = classify_aa_severity(1200, 40000, 50)
    assert severity == "non_severe"


def test_saa_clonal_cytogenetics_warning():
    result = assess({**_base(), "hasClonalCytogenetics": True})
    assert any(
        re.search(r"monosomy|clonal|HCT|transform|cytogenetic", w, re.I)
        for w in result["keyWarnings"]
    )


def test_fanconi_ric_warning():
    result = assess({**_base(), "etiology": "inherited", "inheritedType": "fanconi_anemia"})
    assert any(
        re.search(r"Fanconi|reduced.intensity|RIC|fludarabine", w, re.I)
        for w in result["keyWarnings"]
    )


def test_prior_ist_failure_second_line_options():
    result = assess(
        {
            **_base(),
            "priorIST": True,
            "priorISTResponse": "no_response",
            "donorAvailability": "none",
        }
    )
    assert len(result["secondLineOptions"]) > 0


def test_elderly_saa_no_donor_ist_preferred():
    result = assess({**_base(), "age": 68, "donorAvailability": "none"})
    assert re.search(r"IST|hATG|immunosuppression", result["primaryLabel"], re.I)


def test_bsc_preference_supportive_care():
    result = assess({**_base(), "patientPreference": "bsc"})
    assert re.search(r"supportive|BSC|palliative", result["primaryLabel"], re.I)


# ── Additional branch coverage ──────────────────────────────────────────────

def test_ecog_4_routes_to_bsc():
    result = assess({**_base(), "patientPreference": "aggressive", "ecogPS": 4})
    assert result["primaryRecommendation"] == "bsc_only"


def test_age_40_60_msd_ist_alternative():
    result = assess({**_base(), "age": 50})
    assert result["primaryRecommendation"] == "ist_hatg_csa_eltro"
    assert "MSD-HCT Alternative" in result["primaryLabel"]


def test_nonsevere_no_prior_ist_watch_wait():
    result = assess({**_base(), "severity": "non_severe"})
    assert result["primaryRecommendation"] == "watch_wait"


def test_refractory_with_donor_hct_msd_second_line():
    result = assess(
        {
            **_base(),
            "priorIST": True,
            "priorISTResponse": "relapse",
            "donorAvailability": "hla_matched_sibling",
        }
    )
    assert result["primaryRecommendation"] == "hct_msd_first_line"
    assert result["primaryLabel"] == "Allo-HCT with MSD (Second-Line)"


def test_refractory_haplo_donor():
    result = assess(
        {
            **_base(),
            "priorIST": True,
            "priorISTResponse": "no_response",
            "donorAvailability": "haploidentical",
        }
    )
    assert result["primaryRecommendation"] == "hct_haplo"


def test_partial_response_eltrombopag_mono():
    result = assess(
        {
            **_base(),
            "priorIST": True,
            "priorISTResponse": "partial",
        }
    )
    assert result["primaryRecommendation"] == "eltrombopag_mono"


def test_fallback_clinical_trial():
    # prior IST severe but response "na" -> no branch matches -> fallback
    result = assess({**_base(), "priorIST": True, "priorISTResponse": "na"})
    assert result["primaryRecommendation"] == "clinical_trial"
