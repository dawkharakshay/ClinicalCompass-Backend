"""Influenza Prevention engine — fixtures derived from influenzaPreventionLogic.ts."""

from app.recommendations.modules.influenzaprevention import assess


def _base() -> dict:
    return {
        "ageMonths": 60,
        "isFirstInfluenzaSeason": False,
        "hasChronicLungDisease": False,
        "hasChronicHeartDisease": False,
        "hasImmunosuppression": False,
        "hasHIV": False,
        "hasNeurologicDisorder": False,
        "hasHemoglobinopathy": False,
        "hasDiabetes": False,
        "hasChronicKidneyDisease": False,
        "hasObesity": False,
        "isPregnantAdolescent": False,
        "isResidentLongTermCareFacility": False,
        "hasEggAllergy": False,
        "eggAllergyType": "none",
        "isImmunocompromised": False,
        "hasAsthma": False,
        "hasWheezing": False,
        "receivedInfluenzaVaccinePriorSeason": False,
        "currentSeasonVaccineReceived": False,
        "antiviralIndicationPresent": False,
        "influenzaTestPositive": False,
        "influenzaTestType": "none",
        "symptomsOnsetHours": 0,
        "householdContactHighRisk": False,
    }


def test_healthy_child_standard_risk_laiv():
    r = assess(_base())
    assert r["riskCategory"] == "standard"
    assert r["vaccineType"].startswith("LAIV4 (FluMist) preferred")
    assert r["urgentFlags"] == []
    assert r["evidenceLevel"] == "A"
    assert "INFLUENZA PREVENTION — STANDARD." in r["primaryRecommendation"]
    assert "Age 5 years 0 months." in r["primaryRecommendation"]
    assert "NOT YET RECEIVED" in r["primaryRecommendation"]


def test_infant_under_6_months_cocooning():
    r = assess({**_base(), "ageMonths": 3})
    assert r["riskCategory"] == "high_risk"  # <24 months
    assert r["vaccineType"] == "Not applicable — cocooning strategy"
    assert r["dosesRequired"] == "Not applicable"
    assert any("NOT APPROVED <6 MONTHS" in f for f in r["urgentFlags"])
    # primaryRec is the first urgent flag
    assert r["primaryRecommendation"] == r["urgentFlags"][0]


def test_egg_anaphylaxis_egg_free_vaccine():
    r = assess({**_base(), "eggAllergyType": "anaphylaxis"})
    assert r["vaccineType"].startswith("ccIIV4")
    assert "EGG ANAPHYLAXIS" in r["vaccinationRecommendation"]


def test_asthma_blocks_laiv_iiv4():
    r = assess({**_base(), "hasAsthma": True})
    assert r["riskCategory"] == "standard"  # asthma not in high-risk list
    assert r["vaccineType"].startswith("IIV4")
    assert "asthma/wheezing" in r["vaccinationRecommendation"]


def test_immunocompromised_blocks_laiv_high_risk():
    r = assess({**_base(), "isImmunocompromised": True, "hasImmunosuppression": True})
    assert r["riskCategory"] == "high_risk"
    assert r["vaccineType"].startswith("IIV4")
    assert "immunosuppression" in r["vaccinationRecommendation"]


def test_first_season_two_doses():
    r = assess({**_base(), "isFirstInfluenzaSeason": True,
                "receivedInfluenzaVaccinePriorSeason": False})
    assert r["dosesRequired"].startswith("2 DOSES required")


def test_first_season_but_prior_dose_one_dose():
    r = assess({**_base(), "isFirstInfluenzaSeason": True,
                "receivedInfluenzaVaccinePriorSeason": True})
    assert r["dosesRequired"].startswith("1 DOSE annually")


def test_antiviral_high_risk_within_48h():
    r = assess({**_base(), "ageMonths": 18, "influenzaTestPositive": True,
                "symptomsOnsetHours": 24})
    assert r["riskCategory"] == "high_risk"
    assert "ANTIVIRAL TREATMENT INDICATED (high-risk, symptoms ≤48h)" in r["antiviralRecommendation"]


def test_antiviral_standard_within_48h():
    r = assess({**_base(), "influenzaTestPositive": True, "symptomsOnsetHours": 12})
    assert r["riskCategory"] == "standard"
    assert r["antiviralRecommendation"].startswith("Antiviral treatment: Oseltamivir recommended")


def test_antiviral_high_risk_beyond_48h_flag():
    r = assess({**_base(), "hasDiabetes": True, "influenzaTestPositive": True,
                "symptomsOnsetHours": 72})
    assert r["antiviralRecommendation"].startswith("HIGH-RISK + SYMPTOMS >48h")
    assert any("HIGH-RISK INFLUENZA >48h" in f for f in r["urgentFlags"])


def test_antiviral_empiric_high_risk_test_negative():
    r = assess({**_base(), "hasHIV": True, "influenzaTestPositive": False,
                "antiviralIndicationPresent": True})
    assert r["antiviralRecommendation"].startswith("HIGH-RISK PATIENT with influenza-like illness")


def test_antiviral_not_indicated():
    r = assess(_base())
    assert r["antiviralRecommendation"].startswith("Antiviral treatment not currently indicated")


def test_chemoprophylaxis_household_pep():
    r = assess({**_base(), "householdContactHighRisk": True, "influenzaTestPositive": True})
    assert r["chemoprophylaxisRecommendation"].startswith("POST-EXPOSURE PROPHYLAXIS")
    assert any("HIGH-RISK HOUSEHOLD CONTACT" in f for f in r["urgentFlags"])


def test_chemoprophylaxis_not_indicated():
    r = assess(_base())
    assert r["chemoprophylaxisRecommendation"].startswith("Chemoprophylaxis not routinely indicated")


def test_high_risk_counseling_point_added():
    r = assess({**_base(), "ageMonths": 12})
    assert any("HIGH-RISK CHILD" in c for c in r["counselingPoints"])


def test_rationale_and_primary_rec_render_values():
    r = assess({**_base(), "ageMonths": 26, "currentSeasonVaccineReceived": True})
    assert "Age 26 months." in r["rationale"]
    assert "Risk: standard." in r["rationale"]
    assert "Egg allergy: none." in r["rationale"]
    assert "Immunocompromised: false." in r["rationale"]
    assert "Influenza positive: false." in r["rationale"]
    assert "Symptom onset: 0h." in r["rationale"]
    assert "Age 2 years 2 months." in r["primaryRecommendation"]
    assert "RECEIVED." in r["primaryRecommendation"]
