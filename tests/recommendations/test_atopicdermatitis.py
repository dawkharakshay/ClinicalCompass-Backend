"""Atopic Dermatitis engine — cases ported 1:1 from dermatology.test.ts."""

from app.recommendations.modules.atopicdermatitis import assess


def _base() -> dict:
    return {
        "igaScore": 2,
        "easiScore": 5,
        "pruritusNrs": 3,
        "bsaPercent": 5,
        "ageGroup": "adult",
        "failedTherapy": "none",
        "hasSignificantPruritus": False,
        "hasEczemaHerpeticum": False,
        "hasBacterialSuperinfection": False,
        "hasContactAllergyConfirmed": False,
        "hasOcularDisease": False,
        "hasCardiovascularRisk": False,
        "hasThromboembolismHistory": False,
        "hasMalignancyHistory": False,
        "isPregnantOrPlanning": False,
        "isImmunocompromised": False,
    }


def test_classifies_mild_ad():
    r = assess({**_base(), "igaScore": 2, "easiScore": 5})
    assert r["severity"] == "mild"
    assert len(r["references"]) > 0


def test_classifies_moderate_ad():
    r = assess({
        **_base(),
        "igaScore": 3,
        "easiScore": 20,
        "pruritusNrs": 6,
        "bsaPercent": 15,
        "failedTherapy": "topicals_only",
    })
    assert r["severity"] == "moderate"
    assert r["primaryRecommendation"]
    assert len(r["nextSteps"]) > 0


def test_classifies_severe_ad():
    r = assess({
        **_base(),
        "igaScore": 4,
        "easiScore": 35,
        "pruritusNrs": 8,
        "bsaPercent": 30,
        "failedTherapy": "topicals_and_phototherapy",
        "hasSignificantPruritus": True,
    })
    assert r["severity"] == "severe"
    assert len(r["specificAgents"]) > 0


def test_dupilumab_first_biologic_severe():
    r = assess({
        **_base(),
        "igaScore": 4,
        "easiScore": 40,
        "pruritusNrs": 7,
        "bsaPercent": 35,
        "failedTherapy": "topicals_and_phototherapy",
    })
    agent_text = " ".join(r["specificAgents"]).lower()
    assert "dupilumab" in agent_text


def test_thromboembolism_contraindicates_jak():
    r = assess({
        **_base(),
        "igaScore": 4,
        "easiScore": 38,
        "pruritusNrs": 7,
        "bsaPercent": 30,
        "failedTherapy": "prior_biologic",
        "hasCardiovascularRisk": True,
        "hasThromboembolismHistory": True,
    })
    avoid_text = " ".join(r["agentsToAvoid"]).lower()
    assert "jak" in avoid_text


def test_pregnancy_contraindicates_jak_and_cyclosporine():
    r = assess({
        **_base(),
        "igaScore": 3,
        "easiScore": 22,
        "pruritusNrs": 6,
        "bsaPercent": 18,
        "failedTherapy": "topicals_only",
        "isPregnantOrPlanning": True,
    })
    avoid_text = " ".join(r["agentsToAvoid"]).lower()
    assert "jak" in avoid_text or "cyclosporine" in avoid_text


def test_nemolizumab_for_severe_pruritus():
    r = assess({
        **_base(),
        "igaScore": 4,
        "easiScore": 36,
        "pruritusNrs": 9,
        "bsaPercent": 28,
        "failedTherapy": "topicals_and_phototherapy",
        "hasSignificantPruritus": True,
    })
    pathway_text = r["treatmentPathway"].lower()
    assert "nemolizumab" in pathway_text


def test_evidence_level_and_references():
    r = assess({
        **_base(),
        "igaScore": 3,
        "easiScore": 20,
        "pruritusNrs": 5,
        "bsaPercent": 15,
        "failedTherapy": "none",
    })
    assert r["evidenceLevel"]
    assert len(r["references"]) > 2


def test_string_inputs_coerced():
    # Form submissions arrive as strings; ensure coercion matches TS semantics.
    r = assess({
        **_base(),
        "igaScore": "4",
        "easiScore": "35",
        "pruritusNrs": "8",
        "hasOcularDisease": "true",
    })
    assert r["severity"] == "severe"
    # ocular disease in severe path does NOT add the IL-4/13 avoid line (that is
    # only added in the moderate path), but specificAgents should mention nemolizumab.
    agent_text = " ".join(r["specificAgents"]).lower()
    assert "nemolizumab" in agent_text
