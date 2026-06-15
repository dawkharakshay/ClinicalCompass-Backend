"""Rectal Cancer engine.

Oracle cases ported 1:1 from old_static_code/server/new-modules.test.ts
("Rectal Cancer Logic"), plus fixtures covering the metastatic /
immunotherapy / T2N0 / prior-RT branches.
"""

from app.recommendations.modules.rectalcancer import assess, is_tnt_candidate


def _base() -> dict:
    return {
        "tStage": "T3",
        "nStage": "N1",
        "mStage": "M0",
        "tumorLocation": "lower",
        "mrfStatus": "clear",
        "emviStatus": "negative",
        "tumorSize": 4,
        "age": 58,
        "ecogPS": 0,
        "surgicalFitness": "fit",
        "priorPelvicRT": False,
        "priorChemo": False,
        "responseAssessment": "not_assessed",
        "patientPreference": "no_preference",
        "ibd": False,
        "msi_mmr": "MSS",
    }


# ─── Ported oracle cases (new-modules.test.ts) ────────────────────────────────


def test_identifies_t3n1_as_tnt_candidate():
    from app.recommendations.modules.rectalcancer import _inp

    assert is_tnt_candidate(_inp(_base())) is True


def test_recommends_tnt_for_t3n1():
    r = assess(_base())
    assert r["strategy"] in ("tnt_preferred", "tnt_alternative")
    assert r["evidenceLevel"] is not None


def test_upfront_surgery_for_early_t1n0():
    r = assess({**_base(), "tStage": "T1", "nStage": "N0",
                "mrfStatus": "clear", "emviStatus": "negative"})
    assert r["strategy"] in ("upfront_surgery", "tnt_alternative", "tnt_preferred")


def test_msi_h_flagged_as_key_warning():
    r = assess({**_base(), "msi_mmr": "MSI-H"})
    assert any(
        any(k in w for k in ("MSI", "dMMR", "immunotherapy", "pembrolizumab"))
        for w in r["keyWarnings"]
    )


def test_next_steps_at_least_two():
    r = assess(_base())
    assert len(r["nextSteps"]) >= 2


def test_includes_surgical_approach():
    r = assess(_base())
    assert r["surgicalApproach"] is not None


# ─── Branch-coverage fixtures ─────────────────────────────────────────────────


def test_t3n1_lower_is_tnt_preferred_category1():
    # T3N1 lower: lower&!N0 high-risk feature → tnt_candidate True
    r = assess(_base())
    assert r["strategy"] == "tnt_preferred"
    assert r["evidenceLevel"] == "Category 1"
    assert r["surgicalApproach"] == "apr"  # lower
    # T3 (not T4b/involved/positive) → PRODIGE 23 induction regimen
    assert r["tntRegimen"] == "induction_chemo_crt"


def test_metastatic_msi_h_immunotherapy_first():
    r = assess({**_base(), "mStage": "M1", "msi_mmr": "MSI-H"})
    assert r["strategy"] == "immunotherapy_first"
    assert r["evidenceLevel"] == "Category 1"
    assert r["wwEligible"] is False


def test_metastatic_mss_palliative():
    r = assess({**_base(), "mStage": "M1", "msi_mmr": "MSS"})
    assert r["strategy"] == "palliative"
    assert r["organPreservationScore"] == 0
    assert r["organPreservationLabel"] == "Not applicable (metastatic disease)"


def test_t1n0_local_excision():
    r = assess({**_base(), "tStage": "T1", "nStage": "N0"})
    assert r["strategy"] == "upfront_surgery"
    assert r["surgicalApproach"] == "local_excision"
    assert r["wwEligible"] is False  # responseAssessment not cCR


def test_t1n0_ccr_makes_ww_eligible():
    r = assess({**_base(), "tStage": "T1", "nStage": "N0",
                "responseAssessment": "cCR"})
    assert r["wwEligible"] is True
    assert r["wwCriteria"] == ["cCR after neoadjuvant therapy"]


def test_t2n0_upper_upfront_surgery_lar():
    r = assess({**_base(), "tStage": "T2", "nStage": "N0",
                "tumorLocation": "upper", "mrfStatus": "clear"})
    assert r["strategy"] == "upfront_surgery"
    assert r["surgicalApproach"] == "lar"


def test_t2n0_lower_organ_pref_tnt_alternative():
    r = assess({**_base(), "tStage": "T2", "nStage": "N0",
                "tumorLocation": "lower", "mrfStatus": "clear",
                "patientPreference": "organ_preservation"})
    assert r["strategy"] == "tnt_alternative"
    assert r["surgicalApproach"] == "apr"


def test_t4b_involved_rapido_urgent():
    r = assess({**_base(), "tStage": "T4b", "nStage": "N2",
                "mrfStatus": "involved", "emviStatus": "positive"})
    assert r["strategy"] == "tnt_preferred"
    assert r["tntRegimen"] == "short_course_rt_chemo"  # RAPIDO
    assert r["urgency"] == "urgent"  # T4b + involved
    assert any("MRF involvement" in w for w in r["keyWarnings"])


def test_prior_rt_blocks_tnt_candidate_and_warns():
    r = assess({**_base(), "priorPelvicRT": True})
    # priorPelvicRT → not TNT candidate → tnt_alternative
    assert r["strategy"] == "tnt_alternative"
    assert r["tntRegimen"] is None
    assert any("Prior pelvic RT" in w for w in r["keyWarnings"])


def test_organ_preservation_score_clamped_and_computed():
    # lower(+15) + organ_pref(+10) + cCR(+25) = 100 baseline50 -> 100 (clamped)
    r = assess({**_base(), "responseAssessment": "cCR",
                "patientPreference": "organ_preservation"})
    assert r["organPreservationScore"] == 100
