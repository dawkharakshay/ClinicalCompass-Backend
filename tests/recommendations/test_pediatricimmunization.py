"""Oracle tests for the Pediatric Immunization engine.

Ported 1:1 from old_static_code/server/pediatrics.test.ts
("Pediatric Immunization Logic" describe block).
"""

import re

from app.recommendations.modules.pediatricimmunization import assess

BASE_INPUT = {
    "ageGroup": "9_months",
    "specialPopulation": "none",
    "isPreterm": False,
    "gestationalAgeWeeks": 39,
    "motherHBsAgPositive": False,
    "hasCatchUpNeeds": False,
    "catchUpVaccines": [],
    "hasEggAllergy": False,
    "hasGelatinAllergy": False,
    "hasYeastAllergy": False,
    "isImmunocompromised": False,
    "hivStatus": "negative",
    "hasAsplenia": False,
    "hasSickleCellDisease": False,
    "hasChronicLungDisease": False,
    "hasChronicHeartDisease": False,
    "hasChronicKidneyDisease": False,
    "hasDiabetes": False,
    "isPregnant": False,
    "travelDestination": "none",
    "currentSeason": "off_season",
    "rsvSeasonActive": False,
    "covidVaccinationStatus": "not_started",
}


def _merge(**overrides):
    d = dict(BASE_INPUT)
    d.update(overrides)
    return d


def test_routine_immunization_for_9_month_infant():
    result = assess(BASE_INPUT)
    assert "ROUTINE IMMUNIZATION" in result["primaryRecommendation"]
    assert len(result["references"]) > 0
    assert re.search(r"12 months|Return", result["nextVisitSchedule"], re.IGNORECASE)


def test_scheduled_vaccines_for_12_month_visit():
    result = assess(_merge(ageGroup="12_months"))
    assert len(result["scheduledVaccines"]) > 0
    names = " ".join(v["vaccine"] for v in result["scheduledVaccines"])
    assert re.search(r"MMR|varicella|HepA|PCV", names, re.IGNORECASE)


def test_asplenia_flags_additional_vaccines():
    result = assess(_merge(hasAsplenia=True, specialPopulation="asplenia"))
    all_vaccines = result["scheduledVaccines"] + result["highRiskAdditions"]
    names = " ".join(v["vaccine"] for v in all_vaccines)
    assert re.search(r"PCV|meningococcal|MenACWY", names, re.IGNORECASE)


def test_immunocompromised_laiv_contraindicated():
    result = assess(_merge(isImmunocompromised=True, specialPopulation="immunocompromised"))
    assert re.search(
        r"live|LAIV|immunocompromise", " ".join(result["contraindications"]), re.IGNORECASE
    )


def test_catch_up_schedule_when_has_catch_up_needs():
    result = assess(_merge(hasCatchUpNeeds=True, specialPopulation="catch_up"))
    assert len(result["catchUpVaccines"]) > 0


def test_hiv_positive_flags_live_vaccine_contraindication():
    result = assess(_merge(hivStatus="positive", specialPopulation="immunocompromised"))
    assert re.search(
        r"HIV|live|CONTRAINDICATED", " ".join(result["urgentFlags"]), re.IGNORECASE
    )


# ─── Additional branch coverage (derived from TS branches) ───────────────────


def test_newborn_mother_hbsag_positive_urgent():
    result = assess(_merge(ageGroup="newborn", motherHBsAgPositive=True))
    assert any("HBsAg-positive" in f for f in result["urgentFlags"])
    assert any("HBIG" in v["vaccine"] for v in result["scheduledVaccines"])
    # urgentFlags[0] becomes the primary recommendation prefix
    assert result["primaryRecommendation"].startswith("URGENT: Mother HBsAg-positive")


def test_newborn_default_hepb_and_preterm_precaution():
    result = assess(_merge(ageGroup="newborn", isPreterm=True, gestationalAgeWeeks=32))
    assert any(v["vaccine"] == "Hepatitis B (HepB)" for v in result["scheduledVaccines"])
    assert any("Preterm infant (32 weeks)" in p for p in result["precautions"])


def test_rsv_active_adds_nirsevimab_for_2_months():
    result = assess(_merge(ageGroup="2_months", rsvSeasonActive=True))
    assert any("Nirsevimab" in v["vaccine"] for v in result["scheduledVaccines"])


def test_gelatin_allergy_contraindication():
    result = assess(_merge(hasGelatinAllergy=True))
    assert any("Gelatin allergy" in c for c in result["contraindications"])


def test_covid_shared_decision_when_not_up_to_date():
    result = assess(BASE_INPUT)
    assert any(
        v["vaccine"] == "COVID-19 (updated formulation)"
        for v in result["sharedDecisionVaccines"]
    )


def test_unknown_age_group_falls_back_next_visit():
    result = assess(_merge(ageGroup="24_months"))
    assert result["nextVisitSchedule"].startswith("Annual influenza")
