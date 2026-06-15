"""AMD engine — cases ported 1:1 from old_static_code/server/neuro-ophtho.test.ts."""

from app.recommendations.modules.amd import assess


def _base() -> dict:
    return {
        "stage": "intermediate",
        "affectedEye": "right",
        "cnvType": "not_applicable",
        "visualAcuity": "20/20_to_20/40",
        "antiVEGFHistory": "none",
        "lesionSize": "medium",
        "hasGeographicAtrophy": False,
        "hasPCVorRAP": False,
        "hasSubretinalFluid": False,
        "hasIntraretinalFluid": False,
        "isOnAREDS2Supplements": True,
        "hasDietaryRiskFactors": False,
        "smokingStatus": "never",
        "age": 72,
        "contralateralEyeStatus": "early_amd",
    }


def test_recommends_areds2_for_intermediate():
    r = assess(_base())
    assert "AREDS2" in r["supplementRecommendation"]
    assert "Intermediate AMD" in r["primaryRecommendation"]


def test_flags_areds2_not_started_intermediate():
    r = assess({**_base(), "isOnAREDS2Supplements": False})
    assert any("AREDS2" in f for f in r["urgentFlags"])


def test_urgent_anti_vegf_new_wet_amd():
    r = assess({**_base(), "stage": "advanced_wet", "cnvType": "type2_classic",
                "antiVEGFHistory": "none"})
    assert any("NEW WET AMD" in f for f in r["urgentFlags"])
    assert "Faricimab" in r["antiVEGFSelection"]
    assert "anti-VEGF" in r["primaryRecommendation"]


def test_switch_anti_vegf_suboptimal_response():
    r = assess({**_base(), "stage": "advanced_wet", "cnvType": "type2_classic",
                "antiVEGFHistory": "suboptimal_response"})
    assert "switch" in r["antiVEGFSelection"]
    assert "faricimab" in r["antiVEGFSelection"]


def test_complement_inhibitor_for_geographic_atrophy():
    r = assess({**_base(), "stage": "advanced_dry", "hasGeographicAtrophy": True,
                "gaArea": 3.0})
    assert "Pegcetacoplan" in r["antiVEGFSelection"]
    assert "Geographic atrophy" in r["primaryRecommendation"]


def test_active_smoking_urgent_flag():
    r = assess({**_base(), "smokingStatus": "current"})
    assert any("smoking" in f for f in r["urgentFlags"])


def test_no_areds2_for_early_amd():
    r = assess({**_base(), "stage": "early"})
    assert "NOT indicated" in r["supplementRecommendation"]
    assert "Early AMD" in r["primaryRecommendation"]


def test_evidence_level_a_and_references():
    r = assess(_base())
    assert r["evidenceLevel"] == "A"
    assert len(r["references"]) > 0


# Edge / additional branch coverage derived from TS

def test_current_agent_treat_and_extend():
    r = assess({**_base(), "stage": "advanced_wet", "antiVEGFHistory": "on_aflibercept"})
    assert "Currently on aflibercept" in r["antiVEGFSelection"]
    assert "Continue/optimize current regimen." in r["primaryRecommendation"]
    # not a new wet AMD -> no NEW WET AMD flag
    assert not any("NEW WET AMD" in f for f in r["urgentFlags"])


def test_pcv_rap_appends_to_selection():
    r = assess({**_base(), "stage": "advanced_wet", "antiVEGFHistory": "none",
                "hasPCVorRAP": True})
    assert "PCV/RAP subtype" in r["antiVEGFSelection"]


def test_count_fingers_wet_urgent_flag():
    r = assess({**_base(), "stage": "advanced_wet",
                "visualAcuity": "count_fingers_or_worse", "antiVEGFHistory": "on_faricimab"})
    assert any("Very poor VA" in f for f in r["urgentFlags"])
