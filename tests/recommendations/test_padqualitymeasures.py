"""Ported 1:1 from old_static_code/server/padQM.test.ts.

Oracle tests for the PAD Clinical Performance & Quality Measures engine.
"""

import re

from app.recommendations.modules.padqualitymeasures import (
    PAD_QM_MEASURES,
    assess,
    score_pad_qm_measure,
)


def _measure(mid: str) -> dict:
    return next(m for m in PAD_QM_MEASURES if m["id"] == mid)


BASE_PATIENT = {
    "age": 65,
    "hasDiabetes": False,
    "hasHypertension": False,
    "hasAtherosclerosis": True,
    "padPresentation": "claudication",
    "abiMeasured": False,
    "abiDocumented": False,
    "hadRevascularization": False,
    "onAntiplateletOrAnticoagulant": False,
    "antithromboticTherapyPrescribed": False,
    "antithromboticContraindicated": False,
    "antithromboticDeclined": False,
    "onStatinOrLipidLowering": False,
    "statinPrescribed": False,
    "statinContraindicated": False,
    "statinDeclined": False,
    "onACEInhibitorOrARB": False,
    "aceInhibitorPrescribed": False,
    "aceInhibitorContraindicated": False,
    "aceInhibitorDeclined": False,
    "bpMeasured": False,
    "bpGoalAchieved": False,
    "bpManagementDocumented": False,
    "bpManagementContraindicated": False,
    "bpManagementDeclined": False,
    "hba1cMeasured": False,
    "diabetesManagementDocumented": False,
    "diabetesManagementContraindicated": False,
    "diabetesManagementDeclined": False,
    "tobaccoUseScreened": False,
    "tobaccoUser": False,
    "cessationCounselingProvided": False,
    "cessationPharmacotherapyOffered": False,
    "exerciseTherapyReferralMade": False,
    "exerciseTherapyContraindicated": False,
    "exerciseTherapyDeclined": False,
    "claudicationSymptoms": True,
    "preventiveFootCareProvided": False,
    "footCareContraindicated": False,
    "footCareDeclined": False,
    "hasFootRisk": False,
    "onNovelLipidAgent": False,
    "novelLipidAgentConsidered": False,
    "ldlcAtGoal": False,
    "disparityScreeningDocumented": False,
    "raceEthnicityDocumented": False,
    "socialDeterminantsDocumented": False,
    "multidisciplinaryDiscussionDocumented": False,
    "multidisciplinaryTeamInvolved": False,
    "cltiDiagnosis": False,
}


def patient(**overrides):
    p = dict(BASE_PATIENT)
    p.update(overrides)
    return p


# ─── Measure Registry ─────────────────────────────────────────────────────────


def test_registry_has_15_measures():
    assert len(PAD_QM_MEASURES) == 15
    pms = [m for m in PAD_QM_MEASURES if m["type"] == "performance"]
    qms = [m for m in PAD_QM_MEASURES if m["type"] == "quality"]
    assert len(pms) == 7
    assert len(qms) == 8


def test_registry_ids():
    ids = [m["id"] for m in PAD_QM_MEASURES]
    for i in range(1, 8):
        assert f"PM-{i}" in ids
    for i in range(1, 9):
        assert f"QM-{i}" in ids


def test_registry_new_2026():
    new_measures = [m["id"] for m in PAD_QM_MEASURES if m["isNew2026"]]
    for mid in ["PM-3", "PM-4", "PM-5", "QM-1", "QM-2", "QM-3", "QM-4", "QM-5", "QM-6"]:
        assert mid in new_measures


def test_pm6_pm7_not_new():
    assert _measure("PM-6")["isNew2026"] is False
    assert _measure("PM-7")["isNew2026"] is False


def test_pm6_guideline_class():
    assert _measure("PM-6")["guidelineClass"] == "3_harm"


# ─── PM-1: ABI Testing ────────────────────────────────────────────────────────


def test_pm1_fail_when_abi_not_documented():
    score = score_pad_qm_measure(_measure("PM-1"), patient(abiDocumented=False))
    assert score["result"] == "fail"
    assert score["eligible"] is True


def test_pm1_pass_when_abi_documented():
    score = score_pad_qm_measure(
        _measure("PM-1"),
        patient(abiMeasured=True, abiDocumented=True, ankleArmIndex=0.72),
    )
    assert score["result"] == "pass"


def test_pm1_not_applicable_without_pad():
    score = score_pad_qm_measure(
        _measure("PM-1"),
        patient(hasAtherosclerosis=False, padPresentation="asymptomatic"),
    )
    assert score["result"] == "not_applicable"


# ─── PM-2: Statin Therapy ─────────────────────────────────────────────────────


def test_pm2_fail():
    score = score_pad_qm_measure(_measure("PM-2"), patient())
    assert score["result"] == "fail"


def test_pm2_pass_prescribed():
    score = score_pad_qm_measure(_measure("PM-2"), patient(statinPrescribed=True))
    assert score["result"] == "pass"


def test_pm2_pass_on_med_list():
    score = score_pad_qm_measure(_measure("PM-2"), patient(onStatinOrLipidLowering=True))
    assert score["result"] == "pass"


def test_pm2_excluded_contraindicated():
    score = score_pad_qm_measure(_measure("PM-2"), patient(statinContraindicated=True))
    assert score["result"] == "excluded"
    assert re.search("contraindicated", score["exclusionReason"], re.I)


def test_pm2_excluded_declined():
    score = score_pad_qm_measure(_measure("PM-2"), patient(statinDeclined=True))
    assert score["result"] == "excluded"


# ─── PM-3: Antithrombotic Therapy ─────────────────────────────────────────────


def test_pm3_fail():
    score = score_pad_qm_measure(_measure("PM-3"), patient())
    assert score["result"] == "fail"
    assert score["eligible"] is True


def test_pm3_pass():
    score = score_pad_qm_measure(
        _measure("PM-3"), patient(antithromboticTherapyPrescribed=True)
    )
    assert score["result"] == "pass"


def test_pm3_not_applicable_asymptomatic():
    score = score_pad_qm_measure(
        _measure("PM-3"),
        patient(padPresentation="asymptomatic", hadRevascularization=False),
    )
    assert score["result"] == "not_applicable"


def test_pm3_excluded_contraindicated():
    score = score_pad_qm_measure(
        _measure("PM-3"), patient(antithromboticContraindicated=True)
    )
    assert score["result"] == "excluded"


# ─── PM-4: Blood Pressure Management ──────────────────────────────────────────


def test_pm4_not_applicable_without_htn():
    score = score_pad_qm_measure(_measure("PM-4"), patient(hasHypertension=False))
    assert score["result"] == "not_applicable"


def test_pm4_fail_bp_not_measured():
    score = score_pad_qm_measure(
        _measure("PM-4"), patient(hasHypertension=True, bpMeasured=False)
    )
    assert score["result"] == "fail"


def test_pm4_pass_goal_achieved():
    score = score_pad_qm_measure(
        _measure("PM-4"),
        patient(
            hasHypertension=True,
            bpMeasured=True,
            systolicBP=128,
            bpGoalAchieved=True,
            bpManagementDocumented=True,
        ),
    )
    assert score["result"] == "pass"
    assert re.search("Goal SBP <130 mmHg achieved", score["details"])


def test_pm4_pass_goal_not_achieved():
    score = score_pad_qm_measure(
        _measure("PM-4"),
        patient(
            hasHypertension=True,
            bpMeasured=True,
            systolicBP=145,
            bpGoalAchieved=False,
            bpManagementDocumented=True,
        ),
    )
    assert score["result"] == "pass"
    assert re.search("NOT yet achieved", score["details"])


# ─── PM-5: ACE Inhibitor / ARB ────────────────────────────────────────────────


def test_pm5_fail():
    score = score_pad_qm_measure(_measure("PM-5"), patient())
    assert score["result"] == "fail"


def test_pm5_pass():
    score = score_pad_qm_measure(_measure("PM-5"), patient(aceInhibitorPrescribed=True))
    assert score["result"] == "pass"


def test_pm5_excluded():
    score = score_pad_qm_measure(_measure("PM-5"), patient(aceInhibitorContraindicated=True))
    assert score["result"] == "excluded"


# ─── PM-6: Tobacco Cessation ──────────────────────────────────────────────────


def test_pm6_fail_not_screened():
    score = score_pad_qm_measure(_measure("PM-6"), patient(tobaccoUseScreened=False))
    assert score["result"] == "fail"


def test_pm6_pass_non_user():
    score = score_pad_qm_measure(
        _measure("PM-6"), patient(tobaccoUseScreened=True, tobaccoUser=False)
    )
    assert score["result"] == "pass"


def test_pm6_fail_user_no_counseling():
    score = score_pad_qm_measure(
        _measure("PM-6"),
        patient(
            tobaccoUseScreened=True,
            tobaccoUser=True,
            cessationCounselingProvided=False,
            cessationPharmacotherapyOffered=False,
        ),
    )
    assert score["result"] == "fail"


def test_pm6_pass_user_both():
    score = score_pad_qm_measure(
        _measure("PM-6"),
        patient(
            tobaccoUseScreened=True,
            tobaccoUser=True,
            cessationCounselingProvided=True,
            cessationPharmacotherapyOffered=True,
        ),
    )
    assert score["result"] == "pass"


def test_pm6_fail_user_counseling_only():
    score = score_pad_qm_measure(
        _measure("PM-6"),
        patient(
            tobaccoUseScreened=True,
            tobaccoUser=True,
            cessationCounselingProvided=True,
            cessationPharmacotherapyOffered=False,
        ),
    )
    assert score["result"] == "fail"


# ─── PM-7: Supervised Exercise Therapy ────────────────────────────────────────


def test_pm7_fail():
    score = score_pad_qm_measure(
        _measure("PM-7"),
        patient(claudicationSymptoms=True, exerciseTherapyReferralMade=False),
    )
    assert score["result"] == "fail"


def test_pm7_pass():
    score = score_pad_qm_measure(
        _measure("PM-7"),
        patient(claudicationSymptoms=True, exerciseTherapyReferralMade=True),
    )
    assert score["result"] == "pass"


def test_pm7_not_applicable_clti():
    score = score_pad_qm_measure(
        _measure("PM-7"),
        patient(padPresentation="clti", claudicationSymptoms=False),
    )
    assert score["result"] == "not_applicable"


def test_pm7_excluded_declined():
    score = score_pad_qm_measure(
        _measure("PM-7"),
        patient(claudicationSymptoms=True, exerciseTherapyDeclined=True),
    )
    assert score["result"] == "excluded"


# ─── QM-1: Diabetes Management ────────────────────────────────────────────────


def test_qm1_not_applicable_no_diabetes():
    score = score_pad_qm_measure(_measure("QM-1"), patient(hasDiabetes=False))
    assert score["result"] == "not_applicable"


def test_qm1_fail_no_hba1c():
    score = score_pad_qm_measure(
        _measure("QM-1"), patient(hasDiabetes=True, hba1cMeasured=False)
    )
    assert score["result"] == "fail"


def test_qm1_pass_above_target():
    score = score_pad_qm_measure(
        _measure("QM-1"),
        patient(
            hasDiabetes=True,
            hba1cMeasured=True,
            hba1cValue=7.2,
            diabetesManagementDocumented=True,
        ),
    )
    assert score["result"] == "pass"
    assert re.search("above target", score["details"], re.I)


# ─── QM-2: Preventive Foot Care ───────────────────────────────────────────────


def test_qm2_not_applicable():
    score = score_pad_qm_measure(
        _measure("QM-2"),
        patient(hasDiabetes=False, cltiDiagnosis=False, hasFootRisk=False),
    )
    assert score["result"] == "not_applicable"


def test_qm2_fail_clti():
    score = score_pad_qm_measure(
        _measure("QM-2"),
        patient(cltiDiagnosis=True, preventiveFootCareProvided=False),
    )
    assert score["result"] == "fail"


def test_qm2_pass_diabetic():
    score = score_pad_qm_measure(
        _measure("QM-2"),
        patient(hasDiabetes=True, hasFootRisk=True, preventiveFootCareProvided=True),
    )
    assert score["result"] == "pass"


# ─── QM-3: Novel Lipid-Lowering Therapy ───────────────────────────────────────


def test_qm3_not_applicable_at_goal():
    score = score_pad_qm_measure(
        _measure("QM-3"), patient(ldlcAtGoal=True, ldlcValue=55)
    )
    assert score["result"] == "not_applicable"


def test_qm3_fail():
    score = score_pad_qm_measure(
        _measure("QM-3"),
        patient(ldlcAtGoal=False, ldlcValue=95, novelLipidAgentConsidered=False),
    )
    assert score["result"] == "fail"
    assert re.search(r"95 mg/dL", score["details"])


def test_qm3_pass():
    score = score_pad_qm_measure(
        _measure("QM-3"),
        patient(ldlcAtGoal=False, ldlcValue=88, novelLipidAgentConsidered=True),
    )
    assert score["result"] == "pass"


# ─── QM-4: Health Disparities Assessment ──────────────────────────────────────


def test_qm4_fail_no_race():
    score = score_pad_qm_measure(_measure("QM-4"), patient(raceEthnicityDocumented=False))
    assert score["result"] == "fail"


def test_qm4_fail_no_sdoh():
    score = score_pad_qm_measure(
        _measure("QM-4"),
        patient(raceEthnicityDocumented=True, socialDeterminantsDocumented=False),
    )
    assert score["result"] == "fail"


def test_qm4_pass():
    score = score_pad_qm_measure(
        _measure("QM-4"),
        patient(raceEthnicityDocumented=True, socialDeterminantsDocumented=True),
    )
    assert score["result"] == "pass"


# ─── QM-5: Saphenous Vein Assessment ──────────────────────────────────────────


def test_qm5_not_applicable_endovascular():
    score = score_pad_qm_measure(
        _measure("QM-5"),
        patient(hadRevascularization=True, revascularizationType="endovascular"),
    )
    assert score["result"] == "not_applicable"


def test_qm5_fail():
    score = score_pad_qm_measure(
        _measure("QM-5"),
        patient(
            hadRevascularization=True,
            revascularizationType="surgical",
            saphenousVeinAssessedPreOp=False,
        ),
    )
    assert score["result"] == "fail"


def test_qm5_pass():
    score = score_pad_qm_measure(
        _measure("QM-5"),
        patient(
            hadRevascularization=True,
            revascularizationType="surgical",
            saphenousVeinAssessedPreOp=True,
        ),
    )
    assert score["result"] == "pass"


# ─── QM-6: Multidisciplinary Team Discussion ──────────────────────────────────


def test_qm6_not_applicable():
    score = score_pad_qm_measure(_measure("QM-6"), patient(cltiDiagnosis=False))
    assert score["result"] == "not_applicable"


def test_qm6_fail():
    score = score_pad_qm_measure(
        _measure("QM-6"),
        patient(
            cltiDiagnosis=True,
            padPresentation="clti",
            multidisciplinaryDiscussionDocumented=False,
        ),
    )
    assert score["result"] == "fail"


def test_qm6_pass():
    score = score_pad_qm_measure(
        _measure("QM-6"),
        patient(
            cltiDiagnosis=True,
            padPresentation="clti",
            multidisciplinaryDiscussionDocumented=True,
            multidisciplinaryTeamInvolved=True,
        ),
    )
    assert score["result"] == "pass"


def test_qm6_excluded_ali():
    score = score_pad_qm_measure(
        _measure("QM-6"),
        patient(cltiDiagnosis=True, padPresentation="ali"),
    )
    assert score["result"] == "excluded"


# ─── Full Assessment ──────────────────────────────────────────────────────────


def test_full_15_scores():
    result = assess(patient())
    assert len(result["scores"]) == 15


def test_full_priority_gaps_and_recs():
    result = assess(patient())
    assert len(result["priorityGaps"]) > 0
    assert len(result["recommendations"]) > 0


def test_full_zero_pass_rate():
    result = assess(patient())
    assert result["performanceMeasuresSummary"]["passRate"] == 0


def test_full_well_managed_high_pass_rate():
    well_managed = patient(
        abiMeasured=True,
        abiDocumented=True,
        ankleArmIndex=0.72,
        statinPrescribed=True,
        onStatinOrLipidLowering=True,
        antithromboticTherapyPrescribed=True,
        onAntiplateletOrAnticoagulant=True,
        aceInhibitorPrescribed=True,
        onACEInhibitorOrARB=True,
        tobaccoUseScreened=True,
        tobaccoUser=False,
        exerciseTherapyReferralMade=True,
        raceEthnicityDocumented=True,
        socialDeterminantsDocumented=True,
        ldlcAtGoal=True,
        ldlcValue=58,
        multidisciplinaryDiscussionDocumented=True,
    )
    result = assess(well_managed)
    assert result["performanceMeasuresSummary"]["passRate"] >= 80


def test_full_separate_summaries():
    result = assess(patient())
    assert result["performanceMeasuresSummary"]["total"] == 7
    assert result["qualityMeasuresSummary"]["total"] == 8


def test_full_recommendations_for_failing():
    result = assess(patient())
    assert len(result["recommendations"]) >= 5


def test_full_pm_gaps_before_qm():
    result = assess(patient())
    gap_types = [g["measure"]["type"] for g in result["priorityGaps"]]
    first_qm_index = gap_types.index("quality") if "quality" in gap_types else -1
    last_pm_index = (
        len(gap_types) - 1 - gap_types[::-1].index("performance")
        if "performance" in gap_types
        else -1
    )
    if first_qm_index != -1 and last_pm_index != -1:
        assert last_pm_index < first_qm_index
