"""CRC Screening engine — cases ported 1:1 from gi-modules.test.ts
(describe "assessCRCScreening"), plus branch-coverage fixtures derived
directly from crcScreeningLogic.ts.
"""

import re

from app.recommendations.modules.crcscreening import assess


def _base() -> dict:
    return {
        "ageYears": 50,
        "sex": "male",
        "raceEthnicity": "white",
        "riskCategory": "average_risk",
        "hasFirstDegreeFamilyHistoryCRC": False,
        "hasMultipleFamilyMembersCRC": False,
        "hasSuspectedLynchSyndrome": False,
        "hasConfirmedLynchSyndrome": False,
        "hasConfirmedFAP": False,
        "hasFAPVariant": "none",
        "hasIBD": False,
        "hasPSC": False,
        "hasPersonalHistoryCRC": False,
        "hasPersonalHistoryPolyp": False,
        "hasPersonalHistoryAdvancedAdenoma": False,
        "screeningTestPreference": "colonoscopy",
        "lastColonoscopyYear": None,
        "adenomaHistory": "none",
        "isHighRiskForColonoscopy": False,
    }


# ─── Oracle cases ported 1:1 from gi-modules.test.ts ────────────────────────


def test_colonoscopy_every_10_years_average_risk_50():
    r = assess(_base())
    assert r["primaryRecommendation"]
    assert r["recommendedScreeningTest"]
    assert re.match(r"^[ABC]$", r["evidenceLevel"])


def test_screening_at_age_45_average_risk():
    r = assess({**_base(), "ageYears": 45})
    assert r["primaryRecommendation"]
    assert r["recommendedScreeningTest"]


def test_first_degree_family_history():
    r = assess({
        **_base(),
        "riskCategory": "increased_risk_family_history",
        "hasFirstDegreeFamilyHistoryCRC": True,
        "familyHistoryAge": 52,
    })
    assert r["primaryRecommendation"]
    assert r["recommendedScreeningTest"]


def test_lynch_syndrome_annual_colonoscopy():
    r = assess({
        **_base(),
        "riskCategory": "high_risk_lynch",
        "hasConfirmedLynchSyndrome": True,
        "lynchGene": "MLH1",
    })
    assert r["primaryRecommendation"]
    assert re.search(r"Lynch|annual|1.2 year", r["primaryRecommendation"], re.IGNORECASE)


def test_ibd_unmatched_risk_category_branch():
    # gi-modules.test.ts passes riskCategory "ibd_related" which matches NO
    # branch in the engine -> screening fields stay empty, primaryRecommendation
    # falls through to the default "<risk> — individualized surveillance" string.
    r = assess({
        **_base(),
        "riskCategory": "ibd_related",
        "hasIBD": True,
        "ibdType": "uc",
        "ibdDurationYears": 10,
        "ibdExtent": "pancolitis",
    })
    assert r["primaryRecommendation"]
    assert r["primaryRecommendation"] == "ibd related — individualized surveillance per guideline."
    assert r["recommendedScreeningTest"] == ""


def test_returns_references():
    r = assess(_base())
    assert len(r["references"]) > 0


# ─── Additional branch-coverage fixtures from crcScreeningLogic.ts ──────────


def test_alarm_symptoms_primary_recommendation():
    r = assess({**_base(), "hasRectalBleeding": True})
    assert r["primaryRecommendation"].startswith("ALARM SYMPTOMS")
    assert any("ALARM SYMPTOMS present" in f for f in r["urgentFlags"])
    assert r["nextSteps"][0].startswith("Diagnostic colonoscopy (not screening)")


def test_suspected_lynch_genetic_counseling_flag():
    r = assess({**_base(), "hasSuspectedLynchSyndrome": True})
    assert any("Suspected Lynch syndrome" in f for f in r["urgentFlags"])
    assert "Genetic counseling referral for Lynch syndrome evaluation" in r["nextSteps"]
    assert "Tumor MMR/MSI testing if CRC present" in r["nextSteps"]


def test_psc_plus_ibd_flag():
    r = assess({**_base(), "hasPSC": True, "hasIBD": True})
    assert any("PSC + IBD" in f for f in r["urgentFlags"])


def test_black_african_american_initiation_age():
    r = assess({**_base(), "raceEthnicity": "black_african_american"})
    assert r["screeningInitiationAge"].startswith("Age 40–45")


def test_prefers_noninvasive_fit():
    r = assess({**_base(), "screeningTestPreference": "prefers_noninvasive"})
    assert r["screeningInterval"] == "Annual FIT. Colonoscopy if FIT positive."
    assert "FIT preferred over gFOBT" in r["recommendedScreeningTest"]


def test_prefers_cologuard():
    r = assess({**_base(), "screeningTestPreference": "prefers_cologuard"})
    assert r["screeningInterval"] == "Every 1–3 years (Cologuard). Colonoscopy if positive."
    assert "Cologuard (multitarget stool DNA + FIT)" in r["recommendedScreeningTest"]


def test_default_colonoscopy_branch():
    r = assess(_base())
    assert r["screeningInterval"] == "Every 10 years (colonoscopy). Earlier if polyps found."
    assert r["recommendedScreeningTest"].startswith("Colonoscopy every 10 years")


def test_family_history_under_60():
    r = assess({
        **_base(),
        "riskCategory": "increased_risk_family_history",
        "familyHistoryAge": 52,
    })
    assert r["screeningInitiationAge"].startswith("Age 40 OR 10 years")
    assert r["screeningInterval"] == "Every 5 years (colonoscopy)."


def test_family_history_60_or_older():
    r = assess({
        **_base(),
        "riskCategory": "increased_risk_family_history",
        "familyHistoryAge": 65,
    })
    assert r["screeningInitiationAge"].startswith("Age 40 (ACG 2021)")
    assert r["screeningInterval"] == "Every 5 years (colonoscopy)."


def test_lynch_full_branch():
    r = assess({**_base(), "riskCategory": "high_risk_lynch"})
    assert r["primaryRecommendation"].startswith("Lynch syndrome:")
    assert r["screeningInitiationAge"].startswith("Age 20–25")
    assert "Lynch syndrome surveillance:" in r["surveillanceProtocol"]
    assert any("hereditary cancer program" in f for f in r["urgentFlags"])
    assert r["geneticCounselingIndication"].startswith("Lynch syndrome confirmed or suspected")


def test_fap_full_branch():
    r = assess({**_base(), "riskCategory": "high_risk_fap"})
    assert r["primaryRecommendation"].startswith("FAP:")
    assert r["screeningInitiationAge"].startswith("Age 10–12")
    assert any("colorectal surgery consultation" in f for f in r["urgentFlags"])
    assert r["geneticCounselingIndication"].startswith("FAP confirmed")


def test_ibd_full_branch_no_psc():
    r = assess({**_base(), "riskCategory": "high_risk_ibd"})
    assert r["primaryRecommendation"].startswith("IBD:")
    assert r["screeningInterval"].startswith("Every 1–3 years")


def test_ibd_full_branch_with_psc():
    r = assess({**_base(), "riskCategory": "high_risk_ibd", "hasPSC": True})
    assert r["screeningInterval"] == "Annual colonoscopy (PSC + IBD — very high risk)"


def test_prior_adenoma_low_risk():
    r = assess({
        **_base(),
        "riskCategory": "high_risk_prior_adenoma",
        "adenomaHistory": "low_risk_1_2_tubular",
    })
    assert r["screeningInterval"] == "7–10 years."
    assert "low-risk adenoma" in r["recommendedScreeningTest"]


def test_prior_adenoma_5_plus():
    r = assess({
        **_base(),
        "riskCategory": "high_risk_prior_adenoma",
        "adenomaHistory": "high_risk_5_plus",
    })
    assert r["screeningInterval"] == "1 year."


def test_prior_adenoma_serrated():
    r = assess({
        **_base(),
        "riskCategory": "high_risk_prior_adenoma",
        "adenomaHistory": "sessile_serrated_lesion",
    })
    assert r["screeningInterval"] == "3 years."
    assert "sessile serrated lesion" in r["recommendedScreeningTest"]


def test_prior_crc_branch():
    r = assess({**_base(), "riskCategory": "high_risk_prior_crc"})
    assert r["screeningInitiationAge"] == "Post-CRC surveillance — not initial screening."
    assert "Post-CRC surveillance (ACG 2021)" in r["surveillanceProtocol"]
    assert r["primaryRecommendation"].endswith("individualized surveillance per guideline.")


def test_next_steps_age_45_no_prior_screening():
    r = assess({**_base(), "ageYears": 45, "lastColonoscopyYear": None})
    assert r["nextSteps"][0] == "Initiate CRC screening — age 45+ and no prior screening"


def test_next_steps_below_45():
    r = assess({**_base(), "ageYears": 40})
    assert r["nextSteps"][0].startswith("No screening indicated at this time")
    assert r["primaryRecommendation"].startswith("Below screening age")


def test_rationale_format():
    r = assess({**_base(), "riskCategory": "high_risk_lynch", "hasConfirmedLynchSyndrome": True})
    assert "Risk category: high risk lynch." in r["rationale"]
    assert "Lynch: Confirmed." in r["rationale"]
