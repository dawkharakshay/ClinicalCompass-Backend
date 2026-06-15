"""Low-Grade Glioma engine — fixtures derived from lowGradeGliomaLogic.ts branches.

NOTE: The legacy neurosurgery.test.ts cases for this module were written against
a stale/different input interface (whoGrade, idh1Mutant, codeletion1p19q,
eloquentLocation, etc.) that does not match the current lowGradeGliomaLogic.ts
source interface (idhStatus, extentOfResection, riskCategory, ...). The source
file is the authority for the port, so these fixtures exercise the actual source
branches directly rather than porting the incompatible test inputs verbatim.
"""

from app.recommendations.modules.lowgradeglioma import assess


def _base() -> dict:
    return {
        "idhStatus": "idh_mutant_atrx_mutant",
        "tp53Mutation": False,
        "atrxLoss": True,
        "tertPromoterMutation": False,
        "egfrAmplification": False,
        "chromosome7Gain10Loss": False,
        "tumorSizeCm": "4.0",
        "tumorCrossesMidline": False,
        "eloquentCortexInvolvement": False,
        "contrastEnhancement": False,
        "ageYears": "35",
        "kpsScore": "90",
        "neurologicDeficit": False,
        "seizureAtPresentation": True,
        "extentOfResection": "gross_total",
        "priorRadiotherapy": False,
        "priorChemotherapy": False,
        "riskCategory": "low_risk",
    }


def test_idh_wildtype_with_marker_reclassifies_to_gbm():
    r = assess({**_base(), "idhStatus": "idh_wildtype", "tertPromoterMutation": True})
    assert r["primaryRecommendation"] == "reclassify_as_gbm"
    assert r["molecularDiagnosis"] == "IDH-wildtype Glioblastoma (WHO Grade 4)"
    assert r["evidenceLevel"] == "IA"
    assert any("GBM" in f for f in r["urgentFlags"])


def test_idh_wildtype_egfr_marker_reclassifies():
    r = assess({**_base(), "idhStatus": "idh_wildtype", "egfrAmplification": True})
    assert r["primaryRecommendation"] == "reclassify_as_gbm"


def test_idh_wildtype_chromosome_marker_reclassifies():
    r = assess(
        {**_base(), "idhStatus": "idh_wildtype", "chromosome7Gain10Loss": True}
    )
    assert r["primaryRecommendation"] == "reclassify_as_gbm"


def test_unknown_molecular_status_defers():
    r = assess({**_base(), "idhStatus": "unknown"})
    assert r["primaryRecommendation"] == "multidisciplinary_evaluation"
    assert r["molecularDiagnosis"] == "Pending molecular testing"
    assert any("Do not initiate adjuvant therapy" in w for w in r["warnings"])


def test_low_risk_after_gtr_observation():
    # low_risk, gross_total, age <40, no deficit, small tumor, no midline
    r = assess(_base())
    assert r["primaryRecommendation"] == "observation_after_gtr"
    assert r["evidenceLevel"] == "IIA"
    # idh_mutant_atrx_mutant adds the astrocytoma transformation warning
    assert any("transformation to Grade 3/4" in w for w in r["warnings"])
    assert r["molecularDiagnosis"] == "Astrocytoma, IDH-mutant (WHO Grade 2)"


def test_low_risk_observation_oligo_omits_astro_warning():
    r = assess({**_base(), "idhStatus": "idh_mutant_1p19q_codeleted"})
    assert r["primaryRecommendation"] == "observation_after_gtr"
    assert not any("transformation to Grade 3/4" in w for w in r["warnings"])
    assert "Oligodendroglioma" in r["molecularDiagnosis"]


def test_high_risk_oligodendroglioma_rt_pcv():
    r = assess(
        {
            **_base(),
            "idhStatus": "idh_mutant_1p19q_codeleted",
            "riskCategory": "high_risk",
            "ageYears": "52",
        }
    )
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"
    assert r["recommendationTitle"] == "RT + PCV Chemotherapy — High-Risk LGG"
    assert "Procarbazine" in r["chemotherapyRegimen"]
    assert any("vorasidenib" in a.lower() for a in r["adjuvantTherapy"])


def test_high_risk_astrocytoma_rt_pcv_or_tmz():
    # age >= 40 triggers high risk; astrocytoma path
    r = assess(
        {
            **_base(),
            "idhStatus": "idh_mutant_atrx_mutant",
            "ageYears": "52",
            "neurologicDeficit": True,
        }
    )
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"
    assert r["recommendationTitle"] == "RT + PCV or Temozolomide — High-Risk LGG"
    assert "Temozolomide" in r["chemotherapyRegimen"]


def test_high_risk_biopsy_recommends_reresection():
    r = assess(
        {
            **_base(),
            "extentOfResection": "biopsy",
            "ageYears": "55",
        }
    )
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"
    assert "Biopsy only" in r["surgicalStrategy"]
    assert any("re-resection" in s for s in r["nextSteps"])


def test_high_risk_eloquent_cortex_warning():
    r = assess(
        {
            **_base(),
            "riskCategory": "high_risk",
            "eloquentCortexInvolvement": True,
        }
    )
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"
    assert any("Awake craniotomy" in w for w in r["warnings"])


def test_default_surgery_first_eloquent():
    # Not high risk, but not GTR (subtotal would be high risk) -> use gross_total
    # with deficit? deficit makes high risk. Force default: not high risk,
    # extentOfResection not gross_total -> "gross_total" required for observation.
    # Path: low risk inputs but extentOfResection = "gross_total" fails the
    # observation guard only if age>=40 etc. Use a case that is not high risk and
    # not GTR-low-risk: e.g. gross_total but neurologicDeficit False, age<40 hits
    # observation. To reach default we need not-high-risk AND not the GTR branch.
    # That requires extentOfResection != "gross_total" while still not high risk.
    # subtotal/biopsy are high risk, so the only non-high-risk non-gross_total
    # value is an unrecognized/empty extent.
    r = assess(
        {
            **_base(),
            "extentOfResection": "",
            "eloquentCortexInvolvement": True,
        }
    )
    assert r["primaryRecommendation"] == "surgery_maximal_safe_resection"
    assert "Awake craniotomy" in r["surgicalStrategy"]
    assert r["evidenceLevel"] == "IVB"


def test_high_risk_large_tumor():
    r = assess({**_base(), "tumorSizeCm": "6.5"})
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"


def test_high_risk_midline_crossing():
    r = assess({**_base(), "tumorCrossesMidline": True})
    assert r["primaryRecommendation"] == "rt_plus_pvc_chemotherapy"
