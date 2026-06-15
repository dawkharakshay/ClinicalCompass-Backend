"""High Myopia engine — cases ported 1:1 from
old_static_code/server/neuro-ophtho.test.ts (describe "High Myopia Logic")."""

from app.recommendations.modules.highmyopia import assess


def _base() -> dict:
    return {
        "age": 10,
        "sphericalEquivalent": -4.5,
        "axialLength": "long",
        "myopiaLevel": "moderate",
        "isProgressing": True,
        "myopiaControlHistory": "none",
        "pathologicComplication": "none",
        "hasFamilyHistoryMyopia": True,
        "timeOutdoorsHoursPerDay": 1,
        "screenTimeHoursPerDay": 6,
        "bestCorrectedVA": "20/20",
        "hasMyopicCNV": False,
        "cnvAntiVEGFHistory": "none",
        "isSurgicalCandidateForRefractiveSurgery": False,
        "hasKeratoconus": False,
    }


def test_recommends_atropine_first_line_progressing_childhood():
    r = assess(_base())
    assert "Progressing childhood myopia" in r["primaryRecommendation"]
    assert "atropine" in r["myopiaControlStrategy"]
    assert any("atropine" in s for s in r["nextSteps"])


def test_escalation_when_on_low_dose_atropine():
    r = assess({**_base(), "myopiaControlHistory": "on_atropine_low"})
    assert "atropine" in r["myopiaControlStrategy"]
    assert "orthokeratology" in r["myopiaControlStrategy"]


def test_flags_retinal_detachment_urgent():
    r = assess({**_base(), "pathologicComplication": "retinal_detachment"})
    assert any("RETINAL DETACHMENT" in f for f in r["urgentFlags"])
    assert "Pathologic myopia" in r["primaryRecommendation"]


def test_flags_untreated_myopic_cnv_urgent():
    r = assess({**_base(), "hasMyopicCNV": True, "cnvAntiVEGFHistory": "none"})
    assert any("MYOPIC CNV" in f for f in r["urgentFlags"])
    assert "anti-VEGF" in r["pathologicManagement"]


def test_myopia_control_not_indicated_for_adults():
    r = assess({**_base(), "age": 28, "isProgressing": False})
    assert "not indicated for adults" in r["myopiaControlStrategy"]


def test_recommends_icl_for_extreme_myopia_surgical_candidacy():
    r = assess({
        **_base(),
        "age": 30,
        "sphericalEquivalent": -12,
        "myopiaLevel": "extreme",
        "isSurgicalCandidateForRefractiveSurgery": True,
    })
    assert "ICL" in r["surgicalConsideration"]


def test_flags_keratoconus_lasik_contraindication():
    r = assess({
        **_base(),
        "age": 28,
        "isSurgicalCandidateForRefractiveSurgery": True,
        "hasKeratoconus": True,
    })
    assert any("Keratoconus" in f for f in r["urgentFlags"])
    assert "CONTRAINDICATED" in r["surgicalConsideration"]


def test_returns_evidence_level_a_and_references():
    r = assess(_base())
    assert r["evidenceLevel"] == "A"
    assert len(r["references"]) > 0
