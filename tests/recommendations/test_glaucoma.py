"""Glaucoma engine — fixtures derived 1:1 from the TS branches in
old_static_code/client/src/lib/glaucomaLogic.ts (no TS test file exists)."""

from app.recommendations.modules.glaucoma import assess


def _base() -> dict:
    return {
        "glaucomaType": "poag_mild",
        "iop": 24,
        "cct": 540,
        "cdRatio": 0.6,
        "cdAsymmetry": 0.2,
        "visualFieldStatus": "early_defect",
        "currentTherapy": "none",
        "hasProgressionOnCurrentTherapy": False,
        "age": 65,
        "hasHighMyopia": False,
        "hasDiabetes": False,
        "hasLowCornealHysteresis": False,
        "hasLowOcularPerfusionPressure": False,
        "hasFamilyHistoryGlaucoma": False,
        "isAfricanAmerican": False,
        "hasVascularRiskFactors": False,
        "isSurgicalCandidate": True,
        "contralateralEyeLost": False,
    }


def test_treatment_naive_poag_first_line():
    r = assess(_base())
    assert "Treatment-naive POAG" in r["treatmentStrategy"]
    assert "Prostaglandin analogue (latanoprost 0.005%" in r["firstLineAgent"]
    assert "Selective laser trabeculoplasty (SLT)" in r["laserOption"]
    assert r["surgicalOption"] is None
    assert r["targetIOPRange"].startswith("Target IOP: ≤18 mmHg")
    assert r["evidenceLevel"] == "I"
    assert r["primaryRecommendation"] == "Treatment-naive POAG: Prostaglandin analogue first-line (EMGT, AGIS evidence)."


def test_iop_over_40_urgent_flag():
    r = assess({**_base(), "iop": 45})
    assert any("IOP >40 mmHg" in f for f in r["urgentFlags"])


def test_pacg_acute_angle_closure_flag_and_laser():
    r = assess({**_base(), "glaucomaType": "pacg", "iop": 35})
    assert any("Acute angle closure suspected" in f for f in r["urgentFlags"])
    assert r["laserOption"].startswith("LPI (Nd:YAG)")
    assert r["firstLineAgent"] == "Prostaglandin analogue or beta-blocker post-LPI if IOP target not achieved."
    assert r["targetIOPRange"].startswith("Target IOP: ≤18 mmHg post-LPI")
    # pacg pushes a fellow-eye screen next step
    assert any("Screen fellow eye" in s for s in r["nextSteps"])


def test_split_fixation_flag_and_target():
    # split_fixation only drives the ≤12–15 target when no earlier glaucomaType
    # branch matches; here glaucomaType is poag_severe to reach that branch.
    r = assess({**_base(), "glaucomaType": "poag_severe",
                "visualFieldStatus": "split_fixation"})
    assert any("threatening fixation" in f for f in r["urgentFlags"])
    assert r["targetIOPRange"].startswith("Target IOP: ≤12–15 mmHg")


def test_monocular_patient_flag():
    r = assess({**_base(), "contralateralEyeLost": True})
    assert any("Monocular patient" in f for f in r["urgentFlags"])


def test_severe_poag_progression_surgical_flag():
    # currentTherapy 'one_medication' so the two/three-med branches are skipped and
    # the (progression && poag_severe) OR clause of the maximal-therapy branch fires.
    r = assess({**_base(), "glaucomaType": "poag_severe",
                "currentTherapy": "one_medication",
                "hasProgressionOnCurrentTherapy": True})
    assert any("Severe POAG with documented progression" in f for f in r["urgentFlags"])
    # one_medication+progression branch comes first -> add-second-agent strategy
    assert "Progression on monotherapy" in r["treatmentStrategy"]


def test_severe_poag_progression_maximal_therapy_or_clause():
    # post_slt is not one/two/three-med, so the OR clause (progression && poag_severe)
    # drives the maximal-therapy surgical branch.
    r = assess({**_base(), "glaucomaType": "poag_severe",
                "currentTherapy": "post_slt",
                "hasProgressionOnCurrentTherapy": True})
    assert "Maximal medical therapy with progression" in r["treatmentStrategy"]
    assert r["surgicalOption"].startswith("Trabeculectomy with mitomycin C")


def test_high_risk_oht_treatment():
    # iop 30 (>26), cct 540 (<555), cdRatio 0.6 (>0.5) => ohtsRisk 3 => treat
    r = assess({**_base(), "glaucomaType": "ocular_hypertension",
                "iop": 30, "cct": 540, "cdRatio": 0.6})
    assert "High-risk OHT" in r["treatmentStrategy"]
    assert "Prostaglandin analogue (latanoprost, bimatoprost" in r["firstLineAgent"]
    assert "Ocular hypertension (OHT)" in r["diagnosisConfirmation"]


def test_low_risk_oht_observation():
    # iop 22 (not >26), cct 600 (not <555), cdRatio 0.4 (not >0.5) => risk 0
    r = assess({**_base(), "glaucomaType": "ocular_hypertension",
                "iop": 22, "cct": 600, "cdRatio": 0.4})
    assert "Low-to-moderate risk OHT" in r["treatmentStrategy"]
    assert r["firstLineAgent"] is None
    assert r["targetIOPRange"].startswith("Target IOP: ≤21 mmHg or ≥20% reduction")


def test_ntg_first_line_and_evidence():
    r = assess({**_base(), "glaucomaType": "ntg", "iop": 16,
                "currentTherapy": "none"})
    assert "NTG: Prostaglandin analogue first-line" in r["treatmentStrategy"]
    assert "Avoid beta-blockers" in r["firstLineAgent"]
    assert r["evidenceLevel"] == "II"
    assert r["targetIOPRange"].startswith("Target IOP: ≤12 mmHg")
    assert any("24-hour IOP curve" in s for s in r["nextSteps"])


def test_angle_closure_suspect_laser():
    r = assess({**_base(), "glaucomaType": "angle_closure_suspect"})
    assert "Angle closure suspect" in r["treatmentStrategy"]
    assert r["laserOption"].startswith("Laser peripheral iridotomy (LPI) — Nd:YAG")


def test_progression_on_monotherapy():
    r = assess({**_base(), "currentTherapy": "one_medication",
                "hasProgressionOnCurrentTherapy": True})
    assert "Progression on monotherapy" in r["treatmentStrategy"]
    assert "Add timolol 0.5%" in r["firstLineAgent"]
    assert "SLT if not previously performed" in r["laserOption"]
    assert any("Document progression" in s for s in r["nextSteps"])


def test_progression_on_two_meds_migs():
    r = assess({**_base(), "currentTherapy": "two_medications",
                "hasProgressionOnCurrentTherapy": True})
    assert "Progression on two medications" in r["treatmentStrategy"]
    assert r["surgicalOption"].startswith("MIGS (iStent, Hydrus, GATT)")


def test_three_plus_meds_surgical():
    r = assess({**_base(), "currentTherapy": "three_plus_medications"})
    assert "Maximal medical therapy" in r["treatmentStrategy"]
    assert r["surgicalOption"].startswith("Trabeculectomy with mitomycin C")


def test_continue_current_therapy_default():
    r = assess({**_base(), "currentTherapy": "post_slt",
                "hasProgressionOnCurrentTherapy": False})
    assert r["treatmentStrategy"].startswith("Continue current therapy.")
    assert r["primaryRecommendation"] == "Continue current therapy."


def test_secondary_glaucoma_evidence_level():
    r = assess({**_base(), "glaucomaType": "secondary_glaucoma",
                "currentTherapy": "post_trabeculectomy"})
    assert r["evidenceLevel"] == "II"
    assert "Secondary glaucoma" in r["diagnosisConfirmation"]
    assert r["targetIOPRange"].startswith("Target IOP: Individualize")


def test_rationale_descriptors():
    r = assess({**_base(), "cct": 600, "isAfricanAmerican": True,
                "hasLowCornealHysteresis": True, "hasLowOcularPerfusionPressure": True})
    assert "thick — reduces OHTS risk" in r["rationale"]
    assert "African American race" in r["rationale"]
    assert "Low corneal hysteresis" in r["rationale"]
    assert "Low ocular perfusion pressure" in r["rationale"]
    assert "poag mild" in r["rationale"]


def test_diabetes_high_myopia_next_step():
    r = assess({**_base(), "hasDiabetes": True})
    assert any("Annual dilated fundus exam" in s for s in r["nextSteps"])


def test_string_inputs_coerced():
    # form data arrives as strings
    r = assess({**_base(), "glaucomaType": "ocular_hypertension",
                "iop": "30", "cct": "540", "cdRatio": "0.6"})
    assert "High-risk OHT" in r["treatmentStrategy"]
    assert "IOP: 30 mmHg" in r["rationale"]
    assert "CCT: 540 μm" in r["rationale"]
    assert "C/D ratio: 0.6" in r["rationale"]
