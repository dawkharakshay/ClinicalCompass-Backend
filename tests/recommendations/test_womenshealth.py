"""Ported 1:1 from old_static_code/server/womenshealth.logic.test.ts.

The TypeScript oracle uses nested AssessmentData; the ported engine reads the
interface leaf fields flat, so fixtures are flattened equivalents.
"""

from app.recommendations.modules.womenshealth import assess

# Strong PeVD candidate
STRONG_CANDIDATE = {
    "chronicPelvicPain": True,
    "painDuration": "12",
    "painLocation": "bilateral",
    "exacerbatedByStanding": True,
    "postcoitalPain": True,
    "premenstrualWorsening": True,
    "vulvarVaricosities": True,
    "gravidity": "3",
    "parity": "2",
    "lovDiameter": "6",
    "rovDiameter": "6",
    "lovRefluxDuration": "1500",
    "rovRefluxDuration": "1200",
    "crossPelvicFlow": "present",
    "nutcrackerAngle": "35",
    "pelvicVaricosities": True,
    "uterineVeinDilation": True,
    "dilatedArcuateVeins": "pronounced",
    "mayThurner": False,
}

# Low-score patient - minimal criteria
LOW_SCORE_PATIENT = {
    "chronicPelvicPain": False,
    "painDuration": "0",
    "painLocation": "",
    "exacerbatedByStanding": False,
    "postcoitalPain": False,
    "premenstrualWorsening": False,
    "vulvarVaricosities": False,
    "gravidity": "0",
    "parity": "0",
    "lovDiameter": "3",
    "rovDiameter": "3",
    "lovRefluxDuration": "200",
    "rovRefluxDuration": "200",
    "crossPelvicFlow": "absent",
    "nutcrackerAngle": "90",
    "pelvicVaricosities": False,
    "uterineVeinDilation": False,
    "dilatedArcuateVeins": "none",
    "mayThurner": False,
}


# ── Strong Candidate ──────────────────────────────────────────────
def test_strong_candidate_score_at_least_50():
    assert assess(STRONG_CANDIDATE)["score"] >= 50


def test_strong_candidate_confidence():
    assert assess(STRONG_CANDIDATE)["confidence"] in ("moderate", "high")


def test_strong_candidate_has_treatment_options():
    assert len(assess(STRONG_CANDIDATE)["treatmentOptions"]) > 0


def test_strong_candidate_detects_lov_incompetence():
    assert assess(STRONG_CANDIDATE)["lovIncompetence"] == "detected"


def test_strong_candidate_confirms_pelvic_varicosities():
    assert assess(STRONG_CANDIDATE)["pelvicVaricosities"] == "confirmed"


# ── Low Score Patient ─────────────────────────────────────────────
def test_low_score_patient_low_score():
    assert assess(LOW_SCORE_PATIENT)["score"] < 50


def test_low_score_patient_absent_pelvic_varicosities():
    assert assess(LOW_SCORE_PATIENT)["pelvicVaricosities"] == "absent"


# ── Hemodynamic Criteria ──────────────────────────────────────────
def test_lov_diameter_ge5_contributes():
    with_dilation = {**LOW_SCORE_PATIENT, "lovDiameter": "6"}
    without_dilation = {**LOW_SCORE_PATIENT, "lovDiameter": "3"}
    assert assess(with_dilation)["score"] > assess(without_dilation)["score"]


def test_reflux_over_1000_detects_lov_incompetence():
    with_reflux = {**LOW_SCORE_PATIENT, "lovDiameter": "6", "lovRefluxDuration": "1200"}
    assert assess(with_reflux)["lovIncompetence"] in ("detected", "inconclusive")


# ── Symptom Criteria ──────────────────────────────────────────────
def test_chronic_pelvic_pain_contributes():
    with_pain = {**LOW_SCORE_PATIENT, "chronicPelvicPain": True, "painDuration": "8"}
    assert assess(with_pain)["score"] > assess(LOW_SCORE_PATIENT)["score"]


def test_multiparity_contributes():
    multiparous = {**LOW_SCORE_PATIENT, "gravidity": "3", "parity": "2"}
    assert assess(multiparous)["score"] >= assess(LOW_SCORE_PATIENT)["score"]


# ── Result Structure ──────────────────────────────────────────────
def test_result_has_all_required_fields():
    result = assess(STRONG_CANDIDATE)
    for key in (
        "congestionScore",
        "confidence",
        "lovIncompetence",
        "nutcrackerRisk",
        "pelvicVaricosities",
        "recommendation",
        "treatmentOptions",
        "label",
        "summary",
        "color",
        "score",
        "criteriaMetCount",
        "criteriaTotalCount",
    ):
        assert key in result


def test_criteria_counts_valid():
    result = assess(STRONG_CANDIDATE)
    assert result["criteriaMetCount"] > 0
    assert result["criteriaMetCount"] <= result["criteriaTotalCount"]


# ── Edge / contraindication-style paths derived from TS branches ──
def test_nutcracker_detected_adds_renal_stenting():
    # angle < 25 -> detected; strong candidate already meets >=0.7
    data = {**STRONG_CANDIDATE, "nutcrackerAngle": "20"}
    result = assess(data)
    assert result["nutcrackerRisk"] == "detected"
    assert "Renal vein stenting (Nutcracker)" in result["treatmentOptions"]


def test_low_probability_label_and_color():
    result = assess(LOW_SCORE_PATIENT)
    assert result["label"] == "Low Probability for PeVD"
    assert result["color"] == "destructive"
    assert result["confidence"] == "low"
