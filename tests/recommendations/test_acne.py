"""Tests for the Acne Vulgaris engine.

Cases ported 1:1 from old_static_code/server/dermatology.test.ts (Acne Vulgaris
Logic describe block), plus an edge/contraindication path.
"""

from app.recommendations.modules.acne import assess


def _base(**overrides) -> dict:
    data = {
        "pgaScore": 2,
        "acneType": "comedonal",
        "hasScarring": False,
        "hasPsychosocialBurden": False,
        "patientSex": "male",
        "ageYears": 18,
        "priorTreatment": "none",
        "priorAntibioticMonths": 0,
        "hasPCOS": False,
        "isPregnant": False,
        "isBreastfeeding": False,
        "desireContraception": False,
        "hasHyperkalemiaRisk": False,
        "hasHyperlipidemia": False,
        "hasLiverDisease": False,
        "hasInflammatoryBowelDisease": False,
        "hasDrugInducedAcne": False,
        "hasTrunkInvolvement": False,
        "hasNodulesCysts": False,
    }
    data.update(overrides)
    return data


def test_classifies_mild_comedonal_acne_pga2():
    result = assess(_base(pgaScore=2, acneType="comedonal", ageYears=18))
    assert result["severity"] == "mild"
    assert len(result["references"]) > 0


def test_classifies_moderate_papulopustular_acne_pga3():
    result = assess(
        _base(
            pgaScore=3,
            acneType="papulopustular",
            ageYears=22,
            priorTreatment="topicals_only",
        )
    )
    assert result["severity"] == "moderate"
    assert result["primaryRecommendation"]


def test_indicates_isotretinoin_for_severe_nodulocystic_pga4():
    result = assess(
        _base(
            pgaScore=4,
            acneType="nodulocystic",
            hasScarring=True,
            hasPsychosocialBurden=True,
            ageYears=20,
            priorTreatment="topicals_and_oral_antibiotics",
            priorAntibioticMonths=6,
            hasTrunkInvolvement=True,
            hasNodulesCysts=True,
        )
    )
    assert result["isotretinoinIndicated"] is True
    assert len(result["isotretinoinNotes"]) > 0


def test_flags_antibiotic_stewardship_when_prior_use_exceeds_3_months():
    result = assess(
        _base(
            pgaScore=3,
            acneType="papulopustular",
            ageYears=25,
            priorTreatment="topicals_and_oral_antibiotics",
            priorAntibioticMonths=9,
        )
    )
    assert len(result["antibioticStewardshipNotes"]) > 0


def test_includes_hormonal_options_for_female_with_pcos():
    result = assess(
        _base(
            pgaScore=3,
            acneType="papulopustular",
            patientSex="female",
            ageYears=26,
            priorTreatment="topicals_only",
            hasPCOS=True,
        )
    )
    assert len(result["hormonalOptions"]) > 0
    hormonal_text = " ".join(result["hormonalOptions"]).lower()
    assert "spironolactone" in hormonal_text


def test_flags_isotretinoin_contraindicated_in_pregnancy():
    result = assess(
        _base(
            pgaScore=4,
            acneType="nodulocystic",
            hasScarring=True,
            patientSex="female",
            ageYears=24,
            priorTreatment="topicals_and_oral_antibiotics",
            priorAntibioticMonths=3,
            isPregnant=True,
            hasNodulesCysts=True,
        )
    )
    avoid_text = " ".join(result["agentsToAvoid"]).lower()
    assert "isotretinoin" in avoid_text


def test_returns_evidence_level_and_references():
    result = assess(
        _base(
            pgaScore=3,
            acneType="papulopustular",
            ageYears=22,
            priorTreatment="none",
        )
    )
    assert result["evidenceLevel"]
    assert len(result["references"]) > 2


# Edge / override path: low PGA but scarring escalates to severe + isotretinoin.
def test_low_pga_with_scarring_escalates_to_severe():
    result = assess(_base(pgaScore=1, acneType="papulopustular", hasScarring=True))
    assert result["severity"] == "severe"
    assert result["isotretinoinIndicated"] is True
    # Scarring next-step counseling present
    next_text = " ".join(result["nextSteps"]).lower()
    assert "scarring" in next_text


# Prior-antibiotic message formats the month count without a trailing .0
def test_prior_antibiotic_month_count_formatted_as_integer():
    result = assess(
        _base(
            pgaScore=3,
            acneType="papulopustular",
            priorAntibioticMonths=9,
        )
    )
    notes = " ".join(result["antibioticStewardshipNotes"])
    assert "9 months" in notes
    assert "9.0 months" not in notes
