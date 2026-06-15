"""Tests for the Bone Cancer IO port.

Cases ported 1:1 from old_static_code/server/bonecancer.logic.test.ts. The
legacy entry point takes four objects; the form (and therefore assess) sees the
union of their fields as one flat dict, so each fixture is the merge of the
corresponding TS fixtures.
"""

from __future__ import annotations

from app.recommendations.modules.bonecancer import assess

GOOD_PATIENT = {
    "age": 55,
    "performanceStatus": "1",
    "hasCoagulopathy": False,
    "coagulopathyCorrectible": True,
    "activeInfection": False,
    "medicalComorbidities": [],
}

BONE_METS = {
    "tumorType": "bone-metastases",
    "resectabilityStatus": "resectable",
    "location": "femur",
    "sizeInCm": 3.5,
    "isPainful": True,
    "painSeverity": 7,
    "hasVascularInvolvement": False,
    "priorTreatments": ["chemotherapy"],
    "diseaseStatus": "oligometastatic",
}

PALLIATIVE_PROCEDURE = {
    "treatmentGoal": "palliative",
    "proposedAblationModality": "rfa",
    "combinationTherapy": [],
    "thermalProtectionNeeded": False,
    "criticalStructuresNearby": False,
}

NO_CONTRAINDICATIONS = {
    "uncorrectableCoagulopathy": False,
    "activeInfectionInArea": False,
    "unprotectableCriticalStructures": False,
}

ABSOLUTE_CONTRAINDICATIONS = {
    "uncorrectableCoagulopathy": True,
    "activeInfectionInArea": True,
    "unprotectableCriticalStructures": False,
}


def _merge(*objs: dict) -> dict:
    out: dict = {}
    for o in objs:
        out.update(o)
    return out


# ── Good Candidate ──────────────────────────────────────────────────────────
def test_bone_metastasis_good_io_candidate():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["candidacyLabel"] in ("excellent", "good")


def test_good_candidate_high_score():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["candidacyScore"] >= 60


def test_good_candidate_has_modalities():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert len(result["recommendedModalities"]) > 0


def test_painful_tumor_has_pain_relief_rate():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["expectedOutcomes"]["painReliefRate"] is not None
    assert result["expectedOutcomes"]["painReliefRate"] > 0


# ── Contraindications ───────────────────────────────────────────────────────
def test_uncorrectable_coagulopathy_contraindication():
    result = assess(
        _merge(
            GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, ABSOLUTE_CONTRAINDICATIONS
        )
    )
    assert result["candidacyLabel"] in ("contraindicated", "poor")
    assert len(result["contraindications"]) > 0


def test_active_infection_in_area_contraindication():
    result = assess(
        _merge(
            GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, ABSOLUTE_CONTRAINDICATIONS
        )
    )
    assert len(result["contraindications"]) > 0


# ── Tumor Type Specific ─────────────────────────────────────────────────────
def test_gctb_assessed():
    gctb_tumor = _merge(
        BONE_METS, {"tumorType": "gctb", "resectabilityStatus": "unresectable"}
    )
    result = assess(
        _merge(GOOD_PATIENT, gctb_tumor, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result is not None
    assert result["candidacyScore"] > 0


def test_osteosarcoma_preoperative_embolization():
    osteosarcoma = _merge(
        BONE_METS,
        {
            "tumorType": "osteosarcoma",
            "resectabilityStatus": "resectable",
            "hasVascularInvolvement": True,
        },
    )
    preop = _merge(
        PALLIATIVE_PROCEDURE,
        {"treatmentGoal": "preoperative", "proposedEmbolizationType": "preoperative"},
    )
    result = assess(
        _merge(GOOD_PATIENT, osteosarcoma, preop, NO_CONTRAINDICATIONS)
    )
    assert result is not None


# ── Performance Status ──────────────────────────────────────────────────────
def test_poor_performance_status_reduces_candidacy():
    good_result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    poor_ps = _merge(GOOD_PATIENT, {"performanceStatus": "3"})
    poor_result = assess(
        _merge(poor_ps, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert poor_result["candidacyScore"] <= good_result["candidacyScore"]


# ── Result Structure ────────────────────────────────────────────────────────
def test_result_has_all_required_fields():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    for key in (
        "candidacyScore",
        "candidacyLabel",
        "recommendedModalities",
        "expectedOutcomes",
        "keyConsiderations",
        "contraindications",
        "warnings",
    ):
        assert key in result


def test_expected_outcomes_have_required_metrics():
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    for key in ("technicalSuccessRate", "localControlRate", "complicationRate"):
        assert key in result["expectedOutcomes"]


# ── Additional branch coverage (derived from TS branches) ───────────────────
def test_exact_score_good_candidate():
    # bone-metastases (no score change), resectable+palliative goal (no change),
    # femur (no change), size 3.5 (<=5, no change), painful + severity 7 (+10),
    # priorTreatments only chemotherapy (no +5), PS "1" (no change). => 110 -> 100.
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["candidacyScore"] == 100
    assert result["candidacyLabel"] == "excellent"
    assert result["expectedOutcomes"]["painReliefRate"] == 75


def test_unresectable_relapse_chemo_radiation_scoring():
    # unresectable (+15), spine (+5, thermal), size 8 (>5, -10),
    # painful sev 8 (+10), chemo+radiation (+5), PS "4" (-15) => 100+15+5-10+10+5-15=110 -> 100
    tumor = {
        "tumorType": "bone-metastases",
        "resectabilityStatus": "unresectable",
        "location": "spine",
        "sizeInCm": 8,
        "isPainful": True,
        "painSeverity": 8,
        "hasVascularInvolvement": False,
        "priorTreatments": ["chemotherapy", "radiation"],
        "diseaseStatus": "polymetastatic",
    }
    patient = _merge(GOOD_PATIENT, {"performanceStatus": "4"})
    result = assess(
        _merge(patient, tumor, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["candidacyScore"] == 100
    # spine forces thermal protection consideration
    assert any("Thermal protection" in c for c in result["keyConsiderations"])
    # large tumor + poor PS warnings
    assert any("Large tumor" in w for w in result["warnings"])
    assert any("Poor performance status" in w for w in result["warnings"])


def test_uncorrectable_coagulopathy_zeroes_score():
    # Faithful to TS: contraindication sets score=0 early, but later branches
    # (here painful severity 7 -> +10) still mutate score. The label stays
    # "contraindicated" because the final relabel block is guarded, but the
    # numeric score reflects the +10 (10, not 0).
    result = assess(
        _merge(
            GOOD_PATIENT, BONE_METS, PALLIATIVE_PROCEDURE, ABSOLUTE_CONTRAINDICATIONS
        )
    )
    assert result["candidacyScore"] == 10
    assert result["candidacyLabel"] == "contraindicated"


def test_abc_forces_serial_embolization_approach():
    tumor = _merge(BONE_METS, {"tumorType": "abc"})
    result = assess(
        _merge(GOOD_PATIENT, tumor, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["recommendedApproach"] == "serial"
    assert result["expectedOutcomes"]["localControlRate"] == 75


def test_cryoablation_complication_rate():
    proc = _merge(PALLIATIVE_PROCEDURE, {"proposedAblationModality": "cryoablation"})
    result = assess(
        _merge(GOOD_PATIENT, BONE_METS, proc, NO_CONTRAINDICATIONS)
    )
    assert result["expectedOutcomes"]["complicationRate"] == 2.5


def test_non_painful_omits_pain_relief():
    tumor = _merge(BONE_METS, {"isPainful": False, "painSeverity": 0})
    result = assess(
        _merge(GOOD_PATIENT, tumor, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["expectedOutcomes"]["painReliefRate"] is None


def test_default_tumor_type_modalities():
    tumor = _merge(BONE_METS, {"tumorType": "other"})
    result = assess(
        _merge(GOOD_PATIENT, tumor, PALLIATIVE_PROCEDURE, NO_CONTRAINDICATIONS)
    )
    assert result["recommendedModalities"] == ["rfa", "mwa", "cryoablation"]
