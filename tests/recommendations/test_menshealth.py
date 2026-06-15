"""Ported 1:1 from old_static_code/server/menshealth.logic.test.ts."""

from __future__ import annotations

from app.recommendations.modules.menshealth import assess

# Base assessment - ideal PAE candidate
STRONG_CANDIDATE = {
    "ipssScore": 22,
    "ipssQol": 4,
    "peakFlowRate": "8",
    "postVoidResidual": "150",
    "prostateVolumeOver40": True,
    "failedMedicalTherapy": True,
    "symptomDurationOver6Months": True,
    "urinaryRetentionHistory": False,
    "recurrentUTI": False,
    "recurrentHematuria": False,
    "priorInterventions": [],
    "mriPerformed": True,
    "ctaPerformed": False,
    "middleLobeEnlargement": False,
    "bilateralDisease": True,
    "noProstateCancer": True,
    "noBladderCancer": True,
    "noNeurogenicBladder": True,
    "noUrethralStricture": True,
    "noActiveUTI": True,
    "noCoagulopathy": True,
    "noSevereAtherosclerosis": True,
    "noRenalInsufficiency": True,
}

# Base assessment - not a candidate (exclusion criteria present)
NOT_CANDIDATE = {
    "ipssScore": 8,
    "ipssQol": 1,
    "peakFlowRate": "18",
    "postVoidResidual": "30",
    "prostateVolumeOver40": False,
    "failedMedicalTherapy": False,
    "symptomDurationOver6Months": False,
    "urinaryRetentionHistory": False,
    "recurrentUTI": False,
    "recurrentHematuria": False,
    "priorInterventions": [],
    "mriPerformed": False,
    "ctaPerformed": False,
    "middleLobeEnlargement": False,
    "bilateralDisease": False,
    "noProstateCancer": False,  # Has prostate cancer - exclusion
    "noBladderCancer": True,
    "noNeurogenicBladder": True,
    "noUrethralStricture": True,
    "noActiveUTI": True,
    "noCoagulopathy": True,
    "noSevereAtherosclerosis": True,
    "noRenalInsufficiency": True,
}


# --- Strong Candidate ---
def test_identifies_strong_candidate():
    assert assess(STRONG_CANDIDATE)["label"] == "Strong Candidate"


def test_strong_candidate_high_score():
    assert assess(STRONG_CANDIDATE)["score"] >= 70


def test_strong_candidate_primary_color():
    assert assess(STRONG_CANDIDATE)["color"] == "primary"


# --- Not Indicated ---
def test_not_indicated_when_exclusion_present():
    assert assess(NOT_CANDIDATE)["label"] in ("Not Indicated", "Weak Candidate")


def test_not_indicated_color():
    assert assess(NOT_CANDIDATE)["color"] in ("destructive", "warning")


# --- Moderate Candidate ---
def test_moderate_candidate_partial_criteria():
    moderate = {
        **STRONG_CANDIDATE,
        "failedMedicalTherapy": False,
        "prostateVolumeOver40": False,
        "bilateralDisease": False,
    }
    assert assess(moderate)["label"] in (
        "Moderate Candidate",
        "Weak Candidate",
        "Strong Candidate",
    )


# --- IPSS Severity ---
def test_severe_ipss_contributes():
    severe = {**STRONG_CANDIDATE, "ipssScore": 25}
    mild = {**STRONG_CANDIDATE, "ipssScore": 8, "failedMedicalTherapy": False}
    assert assess(severe)["score"] > assess(mild)["score"]


def test_returns_criteria_counts():
    result = assess(STRONG_CANDIDATE)
    assert result["criteriaMetCount"] > 0
    assert result["criteriaTotalCount"] > 0
    assert result["criteriaMetCount"] <= result["criteriaTotalCount"]


# --- Exclusion Criteria ---
def test_prostate_cancer_exclusion():
    with_cancer = {**STRONG_CANDIDATE, "noProstateCancer": False}
    assert assess(with_cancer)["label"] in ("Not Indicated", "Weak Candidate")


def test_active_uti_exclusion():
    with_uti = {**STRONG_CANDIDATE, "noActiveUTI": False}
    assert assess(with_uti)["label"] in ("Not Indicated", "Weak Candidate")


def test_coagulopathy_reduces_candidacy():
    with_coag = assess({**STRONG_CANDIDATE, "noCoagulopathy": False})
    without_coag = assess(STRONG_CANDIDATE)
    assert with_coag["score"] <= without_coag["score"]
