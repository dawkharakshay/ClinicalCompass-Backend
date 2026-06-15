"""Tests for the RSV Prevention engine.

No TS *.test.ts oracle exists for rsvPreventionLogic.ts; fixtures are derived
directly from the branches of assessRSVPrevention (risk category, nirsevimab,
palivizumab, maternal-vaccine deferral, active infection).
"""

from app.recommendations.modules.rsvprevention import assess


def _base(**over):
    d = {
        "ageMonths": 2,
        "gestationalAgeWeeks": 39,
        "isCurrentRSVSeason": True,
        "isPremature": False,
        "hasCongenitalHeartDisease": False,
        "chdRequiresMedication": False,
        "hasChronicLungDisease": False,
        "requiresSupplementalO2": False,
        "isImmunocompromised": False,
        "hasDownSyndrome": False,
        "hasCysticFibrosis": False,
        "hasNeuromuscularDisease": False,
        "receivedNirsevimabThisSeason": False,
        "receivedPalivizumabThisSeason": False,
        "nirsevimabDosesReceived": 0,
        "motherReceivedRSVVaccine": False,
        "motherVaccinationWeeksBeforeBirth": None,
        "currentlyHospitalized": False,
        "hasActiveRSVInfection": False,
    }
    d.update(over)
    return d


def test_standard_risk_term_infant_in_season():
    r = assess(_base())
    assert r["riskCategory"] == "standard_risk"
    assert r["nirsevimabRecommendation"].startswith("NIRSEVIMAB (BEYFORTUS) RECOMMENDED: All infants <8 months")
    assert r["palivizumabRecommendation"].startswith("Palivizumab not indicated")
    assert r["dosing"].startswith("Nirsevimab: 50mg IM")
    assert r["primaryRecommendation"] == (
        "RSV PREVENTION — STANDARD RISK. Age 2 months. GA 39 weeks. "
        "RSV season ACTIVE. Nirsevimab: NOT YET RECEIVED."
    )
    assert r["urgentFlags"] == []
    assert r["evidenceLevel"] == "A"
    assert len(r["counselingPoints"]) == 6


def test_very_high_risk_immunocompromised():
    r = assess(_base(isImmunocompromised=True))
    assert r["riskCategory"] == "very_high_risk"
    assert r["nirsevimabRecommendation"].startswith("NIRSEVIMAB (BEYFORTUS) RECOMMENDED: High-risk infant")
    assert r["dosing"].startswith("Nirsevimab 200mg IM")
    assert r["palivizumabRecommendation"].startswith("PALIVIZUMAB (SYNAGIS)")
    # high-risk extra counseling point appended
    assert len(r["counselingPoints"]) == 7
    # urgent flag becomes primary; replace only first underscore
    assert r["urgentFlags"][0].startswith("HIGH-RISK RSV: VERY HIGH_RISK")
    assert r["primaryRecommendation"] == r["urgentFlags"][0]


def test_high_risk_preterm_under_29_weeks():
    r = assess(_base(gestationalAgeWeeks=27, isPremature=True))
    assert r["riskCategory"] == "high_risk"
    assert r["urgentFlags"][0].startswith("HIGH-RISK RSV: HIGH RISK")


def test_high_risk_chd_requires_med_ga_above_32():
    # CHD + med + GA>=32 -> high_risk (not very_high since GA not <32)
    r = assess(_base(hasCongenitalHeartDisease=True, chdRequiresMedication=True, gestationalAgeWeeks=35))
    assert r["riskCategory"] == "high_risk"


def test_very_high_risk_chd_requires_med_ga_under_32():
    r = assess(_base(hasCongenitalHeartDisease=True, chdRequiresMedication=True, gestationalAgeWeeks=30))
    assert r["riskCategory"] == "very_high_risk"


def test_moderate_risk_preterm_29_to_34():
    r = assess(_base(isPremature=True, gestationalAgeWeeks=32))
    assert r["riskCategory"] == "moderate_risk"
    assert r["palivizumabRecommendation"].startswith("Palivizumab not indicated")
    assert r["dosing"].startswith("Nirsevimab: 50mg IM")
    assert len(r["counselingPoints"]) == 6


def test_moderate_risk_down_syndrome():
    r = assess(_base(hasDownSyndrome=True))
    assert r["riskCategory"] == "moderate_risk"


def test_over_24_months_not_indicated():
    r = assess(_base(ageMonths=30))
    assert r["nirsevimabRecommendation"].startswith("Nirsevimab not indicated for children >24 months")
    assert r["dosing"] == "Not applicable"


def test_already_received_nirsevimab():
    r = assess(_base(receivedNirsevimabThisSeason=True))
    assert r["nirsevimabRecommendation"].startswith("Nirsevimab already received this RSV season")
    assert r["dosing"] == "Already administered this season."


def test_high_risk_received_nirsevimab_palivizumab_not_needed():
    r = assess(_base(isImmunocompromised=True, receivedNirsevimabThisSeason=True))
    assert r["riskCategory"] == "very_high_risk"
    assert r["palivizumabRecommendation"].startswith("Nirsevimab received — palivizumab not needed")


def test_off_season():
    r = assess(_base(isCurrentRSVSeason=False))
    assert r["nirsevimabRecommendation"].startswith("Not currently RSV season")
    assert r["dosing"] == "Administer at RSV season onset."
    assert "Off-season." in r["primaryRecommendation"]


def test_maternal_vaccine_deferral():
    r = assess(_base(motherReceivedRSVVaccine=True, motherVaccinationWeeksBeforeBirth=3, ageMonths=4))
    assert r["nirsevimabRecommendation"].startswith("MATERNAL RSV VACCINE RECEIVED")


def test_maternal_vaccine_under_2_weeks_no_deferral():
    r = assess(_base(motherReceivedRSVVaccine=True, motherVaccinationWeeksBeforeBirth=1, ageMonths=4))
    assert r["nirsevimabRecommendation"].startswith("NIRSEVIMAB (BEYFORTUS) RECOMMENDED")


def test_maternal_vaccine_but_infant_6mo_no_deferral():
    r = assess(_base(motherReceivedRSVVaccine=True, motherVaccinationWeeksBeforeBirth=3, ageMonths=7))
    assert r["nirsevimabRecommendation"].startswith("NIRSEVIMAB (BEYFORTUS) RECOMMENDED")


def test_active_rsv_infection_primary_and_flag():
    r = assess(_base(hasActiveRSVInfection=True))
    assert r["urgentFlags"][0].startswith("ACTIVE RSV INFECTION: Nirsevimab/palivizumab are PREVENTIVE")
    assert r["primaryRecommendation"] == "ACTIVE RSV INFECTION: Supportive care. Prophylaxis not therapeutic."


def test_rationale_contains_booleans_and_risk():
    r = assess(_base(isCurrentRSVSeason=True, receivedNirsevimabThisSeason=False))
    assert "RSV season: true." in r["rationale"]
    assert "Nirsevimab received: false." in r["rationale"]
    assert "Risk: standard_risk." in r["rationale"]
