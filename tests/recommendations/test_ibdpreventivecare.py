"""Tests for the IBD Preventive Care module.

Ported 1:1 from old_static_code/server/gi-modules.test.ts
(describe "assessIBDPreventiveCare"). The TS baseInput uses some legacy field
names (isFemale/isPregnant, currentImmunosuppression "biologic_monotherapy")
that the assess logic does not read; they are preserved verbatim so the oracle
cases match exactly. Extra branch-coverage fixtures derived from the TS source
are added below the ported oracle cases.
"""

import re

from app.recommendations.modules.ibdpreventivecare import assess

base_input = {
    "ibdType": "uc",
    "ibdDurationYears": 8,
    "ibdExtent": "pancolitis",
    "currentImmunosuppression": "biologic_monotherapy",
    "currentMedications": ["infliximab"],
    "hasHadInfluenzaThisYear": False,
    "hasHadPneumococcalPCV15or20": False,
    "hasHadPneumococcalPPSV23": False,
    "hasHadHepatitisBVaccine": True,
    "hasHadHPVVaccine": False,
    "hasHadVaricellaVaccine": True,
    "hasHadZosterVaccine": False,
    "hasHadMMRVaccine": True,
    "hasHadCOVID19Vaccine": True,
    "hasHadMeningococcalVaccine": False,
    "hasLatentTB": False,
    "hasHepatitisB": False,
    "hasHepatitisBCore": False,
    "hasHepatitisCHistory": False,
    "hasHIV": False,
    "hasHistoplasmosisRisk": False,
    "hasCoccidioidomycosisRisk": False,
    "hasIBDRelatedCancerHistory": False,
    "hasPSC": False,
    "ageYears": 42,
    "isFemale": True,
    "isPregnant": False,
}


# ─── Ported oracle cases ──────────────────────────────────────────────────
def test_recommends_influenza_vaccination_for_immunosuppressed_ibd_patient():
    result = assess(dict(base_input))
    assert result["primaryRecommendation"]
    assert result["vaccinationSchedule"]
    assert re.match(r"^[ABC]$", result["evidenceLevel"])


def test_recommends_crc_surveillance_colonoscopy_for_long_standing_pancolitis():
    result = assess(dict(base_input))
    assert result["cancerSurveillance"]
    assert re.search(r"CRC|colonoscopy|surveillance", result["cancerSurveillance"], re.I)


def test_flags_latent_tb_screening_before_biologic_initiation():
    result = assess({**base_input, "hasLatentTB": True, "currentImmunosuppression": "high"})
    assert any(re.search(r"TB|tuberculosis|LTBI", f, re.I) for f in result["urgentFlags"])


def test_recommends_shingrix_for_immunosuppressed_patients_aged_50_plus():
    result = assess({**base_input, "ageYears": 55, "hasHadZosterVaccine": False})
    assert re.search(r"shingrix|zoster|herpes", result["vaccinationSchedule"], re.I)


def test_returns_references():
    result = assess(dict(base_input))
    assert len(result["references"]) > 0


# ─── Additional branch-coverage fixtures (from TS source) ─────────────────
def test_portal_vein_thrombosis_is_first_urgent_flag_and_primary():
    result = assess({**base_input, "hasPortalVeinThrombosis": True})
    assert result["urgentFlags"][0].startswith("PORTAL VEIN THROMBOSIS")
    assert result["primaryRecommendation"] == result["urgentFlags"][0]
    assert "Portal vein thrombosis: anticoagulation required" in result["thrombosisRiskManagement"]


def test_hepatitis_b_plus_high_immunosuppression_flags_antiviral():
    result = assess({**base_input, "hasHepatitisB": True, "currentImmunosuppression": "combination"})
    assert any("HEPATITIS B + BIOLOGIC" in f for f in result["urgentFlags"])


def test_hepatitis_b_without_high_immunosuppression_no_flag():
    result = assess({**base_input, "hasHepatitisB": True, "currentImmunosuppression": "moderate"})
    assert not any("HEPATITIS B + BIOLOGIC" in f for f in result["urgentFlags"])


def test_prior_dysplasia_urgent_flag():
    result = assess({**base_input, "hasPriorDysplasia": True})
    assert any("Prior dysplasia in IBD" in f for f in result["urgentFlags"])


def test_psc_makes_crc_interval_annual():
    result = assess({**base_input, "hasPSC": True})
    assert "CRC surveillance colonoscopy annual with chromoendoscopy" in result["cancerSurveillance"]


def test_crc_not_recommended_for_short_duration_or_limited_extent():
    result = assess({**base_input, "ibdDurationYears": 5, "ibdExtent": "proctitis"})
    assert "CRC surveillance" not in result["cancerSurveillance"]


def test_cervical_screening_for_female_without_screening():
    result = assess({**base_input, "sex": "female", "hasHadCervicalCancerScreening": False})
    assert "Annual cervical cancer screening" in result["cancerSurveillance"]
    assert "Annual cervical cancer screening (Pap + HPV)" in result["nextSteps"]


def test_thiopurine_lymphoma_warning():
    result = assess({**base_input, "currentMedications": ["Azathioprine"]})
    assert "hepatosplenic T-cell lymphoma" in result["cancerSurveillance"]


def test_skin_exam_recommended_for_high_immunosuppression():
    result = assess({**base_input, "currentImmunosuppression": "high", "hasSkinExamLastYear": False})
    assert "Annual dermatology skin exam" in result["cancerSurveillance"]


def test_combination_immunosuppression_infection_highest_risk_text():
    result = assess({**base_input, "currentImmunosuppression": "combination"})
    assert "HIGHEST RISK: biologic + immunomodulator combination" in result["infectionRiskManagement"]


def test_bone_health_needs_dexa_when_no_recent_dexa():
    result = assess(dict(base_input))
    assert result["boneHealthPlan"].startswith("BONE HEALTH (AGA 2023)")
    assert "DEXA scan for bone density assessment" in result["nextSteps"]


def test_bone_health_up_to_date_when_dexa_recent_and_no_risk():
    result = assess({
        **base_input,
        "hasDEXALastYear": 2025,
        "cumulativeSteroidMonths": 0,
        "hasOsteoporosis": False,
        "hasOsteopenia": False,
    })
    assert result["boneHealthPlan"].startswith("Bone health monitoring up to date")


def test_osteoporosis_adds_bisphosphonate_text():
    result = assess({**base_input, "hasOsteoporosis": True})
    assert "bisphosphonate therapy (alendronate 70mg weekly)" in result["boneHealthPlan"]


def test_hospitalized_with_flare_dvt_prophylaxis_flag():
    result = assess({**base_input, "isHospitalized": True, "hasActiveFlare": True})
    assert any("Hospitalized IBD patient: DVT prophylaxis" in f for f in result["urgentFlags"])
    assert "HOSPITALIZED: LMWH thromboprophylaxis required" in result["thrombosisRiskManagement"]


def test_mental_health_screening_default_recommends_phq9():
    result = assess(dict(base_input))
    assert "PHQ-9 and GAD-7 screening recommended" in result["mentalHealthScreening"]


def test_already_screened_for_depression_text():
    result = assess({**base_input, "hasBeenScreenedForDepression": True})
    assert "Depression/anxiety screening performed" in result["mentalHealthScreening"]


def test_all_vaccines_up_to_date_primary_recommendation():
    result = assess({
        **base_input,
        "hasHadInfluenzaThisYear": True,
        "hasHadPneumococcalPCV15or20": True,
        "hasHadHepatitisBVaccine": True,
        "hasHadHPVVaccine": True,
        "hasHadZosterVaccine": True,
        "hasHadCOVID19Vaccine": True,
    })
    assert result["vaccinationSchedule"].startswith("Vaccination status appears up to date")
    # No urgent flags, no vaccines due -> up-to-date primary recommendation
    assert result["primaryRecommendation"].startswith("IBD preventive care review")


def test_vaccination_items_count_in_primary_recommendation():
    # base_input: influenza, PCV, HPV(<=45) due => 3 items; no urgent flags
    result = assess(dict(base_input))
    assert result["primaryRecommendation"].startswith("3 vaccination(s) due")
