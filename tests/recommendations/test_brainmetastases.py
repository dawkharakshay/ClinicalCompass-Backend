"""Tests for the Brain Metastases Clinical Compass port.

Oracle: old_static_code/client/src/lib/brainMetastasesLogic.ts (assessBrainMetastases).

NOTE: old_static_code/server/neurosurgery.test.ts contains brain-metastases
cases, but they were written against a DIFFERENT/stale interface
(e.g. primaryHistology "nsclc", kpsScore "80_100"/"less_than_50",
metastasisCount "multiple_2_4", fields alkRearrangement/her2Amplification)
that does not match the current brainMetastasesLogic.ts source
(kpsScore "high"/"intermediate"/"low", metastasisCount
"single"/"limited"/"multiple"/"disseminated", alkMutation/her2Positive).
Those cases cannot exercise the real branches, so fixtures here are derived
directly from the TS branches of the source file.
"""

from app.recommendations.modules.brainmetastases import assess


def _base() -> dict:
    return {
        "primaryHistology": "other",
        "metastasisCount": "single",
        "largestLesionCm": 2.0,
        "leptomeningealDisease": False,
        "symptomatic": False,
        "massEffect": False,
        "egfrMutation": False,
        "alkMutation": False,
        "brafV600E": False,
        "her2Positive": False,
        "kpsScore": "high",
        "ageYears": 60,
        "controlledExtracranialDisease": True,
        "extracranialMetastases": False,
        "neurologicDeficit": False,
    }


def test_low_kps_best_supportive_care():
    data = {**_base(), "kpsScore": "low"}
    r = assess(data)
    assert r["primaryRecommendation"] == "best_supportive_care"
    assert r["evidenceLevel"] == "III"
    # BSC short-circuits before histology branches
    assert any("Median OS with KPS <50" in w for w in r["warnings"])


def test_nsclc_egfr_systemic_plus_local():
    data = {**_base(), "primaryHistology": "nsclc_egfr", "egfrMutation": True,
            "metastasisCount": "limited"}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_plus_systemic"
    assert r["evidenceLevel"] == "I"
    assert any("Osimertinib" in s for s in r["systemicTherapyOptions"])
    # limited -> SRS + osimertinib local option, no icotinib
    assert any("SRS + osimertinib" in s for s in r["localTherapyOptions"])
    assert not any("Icotinib" in s for s in r["systemicTherapyOptions"])
    # build helper adds limited SRS local option
    assert any("SRS to limited metastases" in s for s in r["localTherapyOptions"])


def test_nsclc_egfr_multiple_adds_icotinib():
    data = {**_base(), "primaryHistology": "nsclc_egfr", "egfrMutation": True,
            "metastasisCount": "multiple"}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_plus_systemic"
    assert any("Icotinib" in s for s in r["systemicTherapyOptions"])
    assert not any("SRS + osimertinib" in s for s in r["localTherapyOptions"])


def test_nsclc_alk_systemic():
    data = {**_base(), "primaryHistology": "nsclc_alk", "alkMutation": True}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_plus_systemic"
    assert any("Alectinib" in s for s in r["systemicTherapyOptions"])
    assert any("Brigatinib" in s for s in r["systemicTherapyOptions"])


def test_melanoma_braf_targeted():
    data = {**_base(), "primaryHistology": "melanoma_braf", "brafV600E": True,
            "metastasisCount": "limited"}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_plus_systemic"
    assert any("Dabrafenib + trametinib" in s for s in r["systemicTherapyOptions"])


def test_single_large_lesion_surgery_plus_srs():
    data = {**_base(), "metastasisCount": "single", "largestLesionCm": 3.5}
    r = assess(data)
    assert r["primaryRecommendation"] == "surgery_plus_srs"
    assert r["evidenceLevel"] == "II"
    assert len(r["surgicalConsiderations"]) >= 2


def test_single_symptomatic_mass_effect_surgery_plus_srs():
    data = {**_base(), "metastasisCount": "single", "largestLesionCm": 1.5,
            "symptomatic": True, "massEffect": True}
    r = assess(data)
    assert r["primaryRecommendation"] == "surgery_plus_srs"
    # symptomatic + massEffect also raises an urgent flag
    assert any("Symptomatic mass effect" in f for f in r["urgentFlags"])


def test_single_small_srs_alone():
    data = {**_base(), "metastasisCount": "single", "largestLesionCm": 2.0}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_alone"
    assert r["evidenceLevel"] == "I"
    assert any("LITT" in w for w in r["warnings"])


def test_lesion_exactly_3cm_is_surgery():
    # threshold is >= 3
    data = {**_base(), "metastasisCount": "limited", "largestLesionCm": 3.0}
    r = assess(data)
    assert r["primaryRecommendation"] == "surgery_plus_srs"


def test_melanoma_other_adds_immunotherapy_then_srs_alone():
    data = {**_base(), "primaryHistology": "melanoma_other",
            "metastasisCount": "single", "largestLesionCm": 1.0}
    r = assess(data)
    # falls through to single/limited SRS-alone but carries melanoma systemic options
    assert r["primaryRecommendation"] == "srs_alone"
    assert any("Ipilimumab + nivolumab" in s for s in r["systemicTherapyOptions"])
    assert any("Pembrolizumab" in s for s in r["systemicTherapyOptions"])


def test_multiple_actionable_target_systemic_first():
    data = {**_base(), "primaryHistology": "other", "metastasisCount": "multiple",
            "her2Positive": True}
    r = assess(data)
    assert r["primaryRecommendation"] == "srs_plus_systemic"
    assert r["evidenceLevel"] == "II"


def test_multiple_no_target_wbrt():
    data = {**_base(), "primaryHistology": "other", "metastasisCount": "disseminated"}
    r = assess(data)
    assert r["primaryRecommendation"] == "wbrt"
    assert r["evidenceLevel"] == "II"
    assert any("WBRT neurocognitive toxicity" in w for w in r["warnings"])


def test_leptomeningeal_urgent_flag():
    data = {**_base(), "metastasisCount": "single", "leptomeningealDisease": True}
    r = assess(data)
    assert any("Leptomeningeal disease" in f for f in r["urgentFlags"])


def test_default_multidisciplinary():
    # unknown metastasisCount falls through every branch
    data = {**_base(), "primaryHistology": "other", "metastasisCount": "unknown"}
    r = assess(data)
    assert r["primaryRecommendation"] == "multidisciplinary_evaluation"
    assert r["evidenceLevel"] == "III"


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 7
    assert r["references"][0]["pmid"] == "35417433"
