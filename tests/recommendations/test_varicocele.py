"""Varicocele engine — cases ported 1:1 from old_static_code/server/varicocele.test.ts."""

from app.recommendations.modules.varicocele import assess


def _base() -> dict:
    return {
        "age": 32,
        "isAdolescent": False,
        "laterality": "left",
        "grade": "grade2",
        "infertilityDuration": 12,
        "partnerAge": 30,
        "partnerFertilityStatus": "normal",
        "semenQuality": "moderately_abnormal",
        "sdfElevated": False,
        "priorArtFailure": False,
        "nonObstructiveAzoospermia": False,
        "pain": "none",
        "testicularAtrophy": False,
        "atrophyPercent": 0,
        "veinDiameter": 3.5,
        "refluxOnValsalva": True,
        "isolatedRightSided": False,
        "priorTreatment": "none",
        "preferMinimallyInvasive": False,
        "generalAnesthesiaRisk": False,
        "anatomicAccessConcern": False,
    }


# ── subclinical ──

def test_subclinical_no_treatment():
    r = assess({**_base(), "grade": "subclinical"})
    assert r["primaryRecommendation"] == "no_treatment_subclinical"
    assert r["treatmentIndicated"] is False
    assert r["embolizationCandidate"] is False
    assert r["surgeryCandidate"] is False


def test_subclinical_guideline_reference():
    r = assess({**_base(), "grade": "subclinical"})
    assert "AUA/ASRM" in r["guidelineSource"]
    assert r["evidenceLevel"] == "C"


# ── isolated right-sided flag ──

def test_isolated_right_sided_flag():
    r = assess({**_base(), "laterality": "right", "isolatedRightSided": True})
    assert len(r["urgentFlags"]) > 0
    assert "retroperitoneal" in r["urgentFlags"][0]


def test_no_flag_left_sided():
    r = assess({**_base()})
    assert len(r["urgentFlags"]) == 0


# ── NOA pathway ──

def test_noa_multidisciplinary():
    r = assess({**_base(), "semenQuality": "azoospermia", "nonObstructiveAzoospermia": True})
    assert r["primaryRecommendation"] == "multidisciplinary_noa"
    assert r["treatmentIndicated"] is False


def test_noa_microtese_next_steps():
    r = assess({**_base(), "semenQuality": "azoospermia", "nonObstructiveAzoospermia": True})
    assert "micro-TESE" in " ".join(r["nextSteps"])


# ── recurrent after surgery ──

def test_recurrent_after_surgery():
    r = assess({**_base(), "priorTreatment": "prior_surgery_recurrent"})
    assert r["primaryRecommendation"] == "embolization_for_recurrence"
    assert r["embolizationCandidate"] is True
    assert r["treatmentIndicated"] is True


def test_recurrent_notes_cirse():
    r = assess({**_base(), "priorTreatment": "prior_surgery_recurrent"})
    assert "CIRSE" in " ".join(r["embolizationNotes"])


def test_recurrent_tech_notes_present():
    r = assess({**_base(), "priorTreatment": "prior_surgery_recurrent"})
    assert len(r["embolizationTechNotes"]) > 0


# ── fertility indication ──

def test_fertility_indication():
    r = assess({**_base()})
    assert r["treatmentIndicated"] is True
    assert "Infertility" in r["indicationReason"]


def test_no_indication_normal_semen():
    r = assess({**_base(), "semenQuality": "normal", "pain": "none"})
    assert r["treatmentIndicated"] is False
    assert r["primaryRecommendation"] == "observe_monitor"


def test_no_indication_not_trying():
    r = assess({**_base(), "infertilityDuration": 0, "pain": "none"})
    assert r["treatmentIndicated"] is False


# ── pain indication ──

def test_persistent_moderate_pain():
    r = assess({**_base(), "semenQuality": "normal", "infertilityDuration": 0, "pain": "persistent_moderate"})
    assert r["treatmentIndicated"] is True
    assert "pain" in r["indicationReason"]


def test_severe_limiting_pain():
    r = assess({**_base(), "semenQuality": "normal", "infertilityDuration": 0, "pain": "severe_limiting"})
    assert r["treatmentIndicated"] is True


def test_mild_pain_no_indication():
    r = assess({**_base(), "semenQuality": "normal", "infertilityDuration": 0, "pain": "mild_intermittent"})
    assert r["treatmentIndicated"] is False


# ── adolescent atrophy ──

def test_adolescent_atrophy_indication():
    r = assess({
        **_base(),
        "age": 16,
        "isAdolescent": True,
        "infertilityDuration": 0,
        "semenQuality": "normal",
        "pain": "none",
        "testicularAtrophy": True,
        "atrophyPercent": 25,
    })
    assert r["treatmentIndicated"] is True
    assert "atrophy" in r["indicationReason"]


def test_adolescent_atrophy_below_threshold():
    r = assess({
        **_base(),
        "age": 16,
        "isAdolescent": True,
        "infertilityDuration": 0,
        "semenQuality": "normal",
        "pain": "none",
        "testicularAtrophy": False,
        "atrophyPercent": 10,
    })
    assert r["treatmentIndicated"] is False


# ── embolization vs surgery preference ──

def test_embolization_preferred_mi():
    r = assess({**_base(), "preferMinimallyInvasive": True})
    assert r["primaryRecommendation"] == "embolization_preferred"
    assert r["embolizationCandidate"] is True


def test_surgery_preferred():
    r = assess({**_base(), "preferMinimallyInvasive": False, "generalAnesthesiaRisk": False})
    assert r["primaryRecommendation"] == "surgery_preferred"
    assert r["surgeryCandidate"] is True


def test_embolization_preferred_high_risk():
    r = assess({**_base(), "preferMinimallyInvasive": False, "generalAnesthesiaRisk": True})
    assert r["primaryRecommendation"] == "embolization_preferred"


def test_embolization_notes_pmid():
    r = assess({**_base(), "preferMinimallyInvasive": True})
    assert "41137990" in " ".join(r["embolizationNotes"])


def test_surgery_notes_microscopic():
    r = assess({**_base(), "preferMinimallyInvasive": False})
    assert "Microscopic" in " ".join(r["surgeryNotes"])


# ── partner age warning ──

def test_partner_age_warning():
    r = assess({**_base(), "partnerAge": 38})
    assert "37" in " ".join(r["warnings"])


def test_no_partner_age_warning():
    r = assess({**_base(), "partnerAge": 35})
    assert not any("37" in w for w in r["warnings"])


# ── SDF + ART failure ──

def test_sdf_art_failure_indication():
    r = assess({**_base(), "sdfElevated": True, "priorArtFailure": True, "semenQuality": "normal"})
    assert r["treatmentIndicated"] is True
    assert "sperm DNA fragmentation" in r["indicationReason"]


def test_sdf_alone_no_indication():
    r = assess({
        **_base(),
        "sdfElevated": True,
        "priorArtFailure": False,
        "semenQuality": "normal",
        "infertilityDuration": 0,
        "pain": "none",
    })
    assert r["treatmentIndicated"] is False


# ── bilateral technical note ──

def test_bilateral_tech_note():
    r = assess({**_base(), "laterality": "bilateral", "preferMinimallyInvasive": True})
    assert "Bilateral" in " ".join(r["embolizationTechNotes"])


# ── anatomic access concern warning ──

def test_anatomic_access_warning():
    r = assess({**_base(), "anatomicAccessConcern": True})
    assert "8–30%" in " ".join(r["warnings"])


# ── observe_monitor ──

def test_observe_monitor():
    r = assess({
        **_base(),
        "semenQuality": "normal",
        "infertilityDuration": 0,
        "pain": "none",
        "testicularAtrophy": False,
        "sdfElevated": False,
        "priorArtFailure": False,
    })
    assert r["primaryRecommendation"] == "observe_monitor"
    assert r["treatmentIndicated"] is False
    assert r["embolizationCandidate"] is False
    assert r["surgeryCandidate"] is False
