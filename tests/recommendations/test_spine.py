"""Oracle tests for the Spine module.

Cases 1:1 ported from old_static_code/server/new-modules.test.ts (Spine Logic).
Additional cases derived from the TS branches to pin each major decision path.
"""

from __future__ import annotations

from app.recommendations.modules.spine import assess


BASE = {
    "condition": "lumbar_disc_herniation",
    "neurologicStatus": "radiculopathy_only",
    "painDurationWeeks": 8,
    "painSeverityVAS": 6,
    "functionalImpairment": "moderate",
    "conservativeTrialDuration": "6_to_12_weeks",
    "conservativeTreatmentsTrialed": ["PT", "NSAIDs"],
    "imagingFindings": "disc_herniation",
    "imagingClinicalCorrelation": True,
    "cauda_equina_syndrome": False,
    "progressiveNeurologicDeficit": False,
    "spinalInstability": False,
    "malignancy": False,
    "infection": False,
    "fracture": False,
    "age": 48,
    "smoker": False,
    "obesity": False,
    "diabetes": False,
    "osteoporosis": False,
    "psychosocialFactors": False,
    "priorSpineSurgery": False,
    "patientPrefersSurgery": False,
}


def _input(**overrides):
    d = dict(BASE)
    d.update(overrides)
    return d


# ─── Oracle cases (ported 1:1) ────────────────────────────────────────────────


def test_conservative_for_disc_herniation_without_red_flags():
    result = assess(_input())
    assert result["decision"] in ("continue_conservative", "surgery_optional")
    assert result["evidenceLevel"]


def test_urgent_surgery_for_cauda_equina():
    result = assess(_input(cauda_equina_syndrome=True))
    assert result["decision"] == "surgery_urgent"


def test_urgent_surgery_for_progressive_deficit():
    result = assess(
        _input(neurologicStatus="progressive_deficit", progressiveNeurologicDeficit=True)
    )
    assert result["decision"] == "surgery_urgent"


def test_surgery_after_failed_conservative_trial():
    result = assess(
        _input(
            conservativeTrialDuration="more_than_12_weeks",
            conservativeTreatmentsTrialed=["PT", "NSAIDs", "epidural"],
        )
    )
    assert result["decision"] in (
        "surgery_optional",
        "surgery_recommended",
        "continue_conservative",
    )


def test_no_surgery_for_axial_lbp_without_structural_cause():
    result = assess(
        _input(
            condition="lumbar_degenerative_disc",
            neurologicStatus="intact",
            imagingFindings="disc_bulge_only",
            imagingClinicalCorrelation=False,
        )
    )
    assert result["decision"] in (
        "continue_conservative",
        "surgery_not_recommended",
        "multidisciplinary_pain",
    )


def test_returns_keywarnings_array():
    result = assess(_input())
    assert isinstance(result["keyWarnings"], list)


# ─── Branch-specific fidelity cases ───────────────────────────────────────────


def test_cauda_equina_emergent_exact():
    result = assess(_input(cauda_equina_syndrome=True))
    assert result["decision"] == "surgery_urgent"
    assert result["urgency"] == "emergent"
    assert result["decisionLabel"] == "EMERGENT Surgical Decompression"
    # choosingWiselyFlags is suppressed in the emergent branch
    assert result["choosingWiselyFlags"] == []
    assert (
        "Cauda equina syndrome — EMERGENT surgical decompression required"
        in result["redFlagsPresent"]
    )


def test_cauda_equina_via_neurologic_status():
    result = assess(_input(neurologicStatus="cauda_equina"))
    assert result["decision"] == "surgery_urgent"
    assert result["urgency"] == "emergent"


def test_severe_myelopathy_urgent_cervical_procedure():
    result = assess(
        _input(condition="cervical_myelopathy", neurologicStatus="myelopathy_severe")
    )
    assert result["decision"] == "surgery_urgent"
    assert result["urgency"] == "urgent"
    assert result["surgicalProcedure"] == (
        "Cervical decompression (ACDF or posterior laminectomy/fusion) — within 1-2 weeks"
    )


def test_progressive_deficit_lumbar_procedure():
    result = assess(_input(progressiveNeurologicDeficit=True))
    assert result["surgicalProcedure"] == "Lumbar decompression — within 1-2 weeks"


def test_cervical_myelopathy_mild_recommended():
    result = assess(
        _input(condition="cervical_myelopathy", neurologicStatus="myelopathy_mild")
    )
    assert result["decision"] == "surgery_recommended"
    assert result["urgency"] == "elective"
    assert result["keyWarnings"] == []


def test_cervical_myelopathy_moderate_warnings_filtered():
    result = assess(
        _input(
            condition="cervical_myelopathy",
            neurologicStatus="myelopathy_moderate",
            psychosocialFactors=True,
            smoker=True,
        )
    )
    assert result["decision"] == "surgery_recommended"
    assert result["keyWarnings"] == [
        "Psychosocial factors present: address before surgery — impacts recovery",
        "Smoking cessation: reduces pseudarthrosis risk after ACDF by 50%",
    ]


def test_disc_herniation_inadequate_trial_conservative():
    result = assess(_input(conservativeTrialDuration="less_than_6_weeks"))
    assert result["decision"] == "continue_conservative"
    assert result["decisionLabel"] == "Continue Conservative Treatment (6-12 weeks)"
    assert len(result["nextSteps"]) == 3
    # inadequate trial + no red flags => choosing wisely "no adequate trial" flag present
    assert any("adequate conservative trial" in f for f in result["choosingWiselyFlags"])


def test_disc_herniation_adequate_trial_surgery_optional():
    result = assess(_input(conservativeTrialDuration="more_than_12_weeks"))
    assert result["decision"] == "surgery_optional"
    assert result["surgicalProcedure"] == "Lumbar microdiscectomy (minimally invasive preferred)"


def test_disc_herniation_optional_warnings_obesity_smoker():
    result = assess(
        _input(
            conservativeTrialDuration="6_to_12_weeks",
            smoker=True,
            obesity=True,
            psychosocialFactors=True,
        )
    )
    assert result["keyWarnings"] == [
        "Psychosocial factors: poor predictor of surgical outcome — address before surgery",
        "Smoking: increases risk of recurrence and poor healing",
        "Obesity (BMI ≥35): higher surgical complication risk — weight loss before elective surgery recommended",
    ]


def test_lumbar_stenosis_inadequate_trial_conservative():
    result = assess(
        _input(
            condition="lumbar_stenosis",
            neurologicStatus="intact",
            conservativeTrialDuration="none",
        )
    )
    assert result["decision"] == "continue_conservative"
    assert result["decisionLabel"] == "Continue Conservative Treatment"


def test_lumbar_stenosis_adequate_trial_recommended():
    result = assess(
        _input(
            condition="lumbar_stenosis",
            neurologicStatus="intact",
            conservativeTrialDuration="6_to_12_weeks",
        )
    )
    assert result["decision"] == "surgery_recommended"
    assert result["urgency"] == "elective"


def test_lumbar_stenosis_inadequate_trial_with_red_flag_goes_surgical():
    # red flag (malignancy) bypasses the conservative branch even with no trial
    result = assess(
        _input(
            condition="lumbar_stenosis",
            neurologicStatus="intact",
            conservativeTrialDuration="none",
            malignancy=True,
        )
    )
    assert result["decision"] == "surgery_recommended"


def test_lumbar_stenosis_osteoporosis_warning():
    result = assess(
        _input(
            condition="lumbar_stenosis",
            neurologicStatus="intact",
            conservativeTrialDuration="more_than_12_weeks",
            osteoporosis=True,
        )
    )
    assert result["keyWarnings"] == [
        "Fusion not routinely added to decompression — increases complication risk without benefit unless instability present",
        "Osteoporosis: increases hardware failure risk — optimize bone density before surgery",
    ]


def test_ddd_intact_not_recommended():
    result = assess(
        _input(condition="lumbar_degenerative_disc", neurologicStatus="intact")
    )
    assert result["decision"] == "surgery_not_recommended"
    assert result["urgency"] == "not_indicated"
    # choosing wisely DDD-without-radiculopathy flag must be present
    assert any(
        "degenerative disc disease without radiculopathy" in f
        for f in result["choosingWiselyFlags"]
    )


def test_default_conservative_branch():
    # condition with no specific handler falls to default
    result = assess(
        _input(condition="lumbar_spondylolisthesis", neurologicStatus="intact")
    )
    assert result["decision"] == "continue_conservative"
    assert result["decisionLabel"] == "Conservative Management Recommended"


def test_choosing_wisely_imaging_under_6_weeks():
    result = assess(
        _input(
            painDurationWeeks=4,
            imagingFindings="disc_herniation",
            conservativeTrialDuration="6_to_12_weeks",
        )
    )
    assert any("<6 weeks without red flags" in f for f in result["choosingWiselyFlags"])


def test_choosing_wisely_imaging_no_correlation_with_preference():
    result = assess(
        _input(
            imagingClinicalCorrelation=False,
            patientPrefersSurgery=True,
            conservativeTrialDuration="6_to_12_weeks",
        )
    )
    assert any(
        "without clinical correlation" in f for f in result["choosingWiselyFlags"]
    )


def test_psychosocial_choosing_wisely_flag():
    result = assess(_input(psychosocialFactors=True))
    assert any("yellow flags" in f for f in result["choosingWiselyFlags"])
