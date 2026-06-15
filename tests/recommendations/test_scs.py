"""SCS engine — fixtures derived directly from scsLogic.ts branches."""

from app.recommendations.modules.scs import assess


def _base() -> dict:
    return {
        "age": "",
        "phase": "trial",
        "symptomDurationMonths": "0",
        "painScore": "0",
        "indications": [],
        "conservativeTherapies": [],
        "contraindications": [],
        "trialReliefPercent": "0",
        "psychologicalClearance": False,
        "priorTrialSuccess": False,
    }


def test_hard_contraindication_wins():
    r = assess({**_base(), "phase": "implant", "contraindications": ["coagulopathy", "mri-dependent"]})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "SCS Contraindicated"
    assert r["contraindications"] == ["Uncorrectable coagulopathy"]
    assert r["optimizationSteps"] == [
        "Address all contraindications",
        "Psychiatric evaluation and treatment if needed",
    ]


def test_implant_class_i():
    r = assess({
        **_base(),
        "phase": "implant",
        "priorTrialSuccess": True,
        "trialReliefPercent": "60",
        "psychologicalClearance": True,
        "indications": ["fbss"],
    })
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Permanent SCS Implant Recommended"
    assert r["loe"] == "A"  # fbss


def test_implant_no_prior_trial():
    r = assess({**_base(), "phase": "implant", "priorTrialSuccess": False})
    assert r["cor"] == "III"
    assert r["urgency"] == "Trial Required First"
    assert r["recommendation"] == "SCS Not Indicated"
    assert any("Perform SCS trial" in s for s in r["optimizationSteps"])


def test_implant_trial_relief_too_low():
    r = assess({
        **_base(),
        "phase": "implant",
        "priorTrialSuccess": True,
        "trialReliefPercent": "40",
        "psychologicalClearance": True,
    })
    assert r["cor"] == "III"
    assert r["urgency"] == "Trial Unsuccessful"


def test_implant_needs_psych_clearance():
    r = assess({
        **_base(),
        "phase": "implant",
        "priorTrialSuccess": True,
        "trialReliefPercent": "60",
        "psychologicalClearance": False,
    })
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Psychological Clearance Required"
    assert r["recommendation"] == "Additional Requirements Needed"


def test_trial_class_i():
    r = assess({
        **_base(),
        "phase": "trial",
        "indications": ["crps"],
        "conservativeTherapies": ["pt", "meds", "injections"],
        "symptomDurationMonths": "6",
        "psychologicalClearance": True,
        "painScore": "8",
    })
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "SCS Trial Recommended"
    assert r["loe"] == "A"  # crps
    assert any("Severe pain (NRS ≥7)" in s for s in r["rationale"])


def test_trial_psych_clearance_needed():
    r = assess({
        **_base(),
        "phase": "trial",
        "indications": ["radiculopathy"],
        "conservativeTherapies": ["pt", "meds", "injections"],
        "symptomDurationMonths": "6",
        "psychologicalClearance": False,
    })
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Psychological Clearance Needed"
    assert r["recommendation"] == "SCS Reasonable"
    assert r["loe"] == "B"  # neuropathic, not fbss/crps


def test_trial_insufficient_conservative():
    r = assess({
        **_base(),
        "phase": "trial",
        "indications": ["fbss"],
        "conservativeTherapies": ["pt"],
        "symptomDurationMonths": "6",
        "psychologicalClearance": True,
    })
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Conservative Therapy"


def test_trial_insufficient_criteria():
    # adequate conservative but no qualifying indication and psych cleared
    r = assess({
        **_base(),
        "phase": "trial",
        "indications": ["other"],
        "conservativeTherapies": ["pt", "meds", "injections"],
        "symptomDurationMonths": "6",
        "psychologicalClearance": True,
    })
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"


def test_revision_class_iia():
    r = assess({**_base(), "phase": "revision"})
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "SCS Reasonable"
    assert any("revision/replacement" in s for s in r["rationale"])


def test_mri_dependent_optimization_step():
    r = assess({
        **_base(),
        "phase": "revision",
        "contraindications": ["mri-dependent"],
    })
    assert any("MRI-compatible" in s for s in r["optimizationSteps"])
    # non-absolute contraindication preserved in output
    assert r["contraindications"] == ["mri-dependent"]
