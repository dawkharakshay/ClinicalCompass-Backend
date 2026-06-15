"""Vertebroplasty / Kyphoplasty engine — fixtures derived directly from
vertebroplastyLogic.ts branches."""

from app.recommendations.modules.vertebroplasty import assess


def _base() -> dict:
    return {
        "age": "70",
        "procedureType": "",
        "fractureLevel": "L1",
        "fractureLevels": [],
        "fractureAgeWeeks": "0",
        "vasScore": "0",
        "oswestryScore": "0",
        "acuteOnset": False,
        "mriEdema": False,
        "ctFractureLine": False,
        "heightLoss": "0",
        "kyphosisAngle": "0",
        "posteriorWallIntact": True,
        "osteoporosis": False,
        "malignancy": False,
        "trauma": False,
        "conservativeWeeks": "0",
        "bedRestDays": "0",
        "analgesicsUsed": False,
        "braceUsed": False,
        "activeInfection": False,
        "coagulopathy": False,
        "spinalCordCompression": False,
        "radiculopathy": False,
        "allergy": False,
        "pregnancy": False,
    }


def test_contraindication_active_infection():
    r = assess({**_base(), "activeInfection": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Vertebral Augmentation Contraindicated"
    assert r["procedureNote"] == ""
    assert any("Active systemic or local infection" in c for c in r["contraindications"])


def test_contraindications_multiple():
    r = assess({**_base(), "coagulopathy": True, "pregnancy": True, "allergy": True,
                "spinalCordCompression": True})
    assert r["cor"] == "III"
    assert len(r["contraindications"]) == 4


def test_class_i_acute_expedited():
    r = assess({**_base(), "mriEdema": True, "fractureAgeWeeks": "2", "vasScore": "7",
                "osteoporosis": True, "posteriorWallIntact": True, "conservativeWeeks": "3"})
    assert r["cor"] == "I"
    assert r["urgency"] == "Acute Fracture — Expedited"
    assert r["loe"] == "A"
    assert r["recommendation"] == "Vertebral Augmentation Recommended"
    assert any("Osteoporotic vertebral compression fracture" in s for s in r["rationale"])
    assert any("VAS pain score 7/10" in s for s in r["rationale"])


def test_class_i_subacute_appropriate_malignancy_short_conservative():
    r = assess({**_base(), "mriEdema": True, "fractureAgeWeeks": "5", "vasScore": "8",
                "malignancy": True, "posteriorWallIntact": True, "conservativeWeeks": "1"})
    assert r["cor"] == "I"
    assert r["urgency"] == "Subacute Fracture — Appropriate"
    assert r["loe"] == "A"
    assert any("Pathologic fracture from malignancy" in s for s in r["rationale"])
    # short conservative trial note + optimization step
    assert any("Short conservative therapy trial" in s for s in r["rationale"])
    assert any("Document failed conservative therapy" in s for s in r["optimizationSteps"])


def test_class_iia_reasonable():
    r = assess({**_base(), "ctFractureLine": True, "fractureAgeWeeks": "10", "vasScore": "5",
                "conservativeWeeks": "4", "posteriorWallIntact": True})
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["loe"] == "B"  # mriEdema False
    assert r["recommendation"] == "Vertebral Augmentation Reasonable"
    assert any("Conservative therapy trial: 4 weeks" in s for s in r["rationale"])


def test_class_iib_chronic_with_edema():
    r = assess({**_base(), "mriEdema": True, "fractureAgeWeeks": "20", "vasScore": "6",
                "conservativeWeeks": "8"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Chronic Fracture with Persistent Edema"
    assert r["loe"] == "B"  # fractureWeeks > 6
    assert r["recommendation"] == "Insufficient Criteria for Vertebral Augmentation"
    assert any("chronic fracture" in s for s in r["rationale"])


def test_class_iib_imaging_required():
    r = assess({**_base(), "mriEdema": False, "ctFractureLine": False,
                "fractureAgeWeeks": "3", "vasScore": "6"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Imaging Evidence Required"
    assert r["recommendation"] == "MRI/CT Imaging Required Before Proceeding"
    assert any("STIR/fat-suppressed" in s for s in r["optimizationSteps"])


def test_class_iib_continue_conservative():
    # imaging present (ctFractureLine) but VAS < 4 so not IIa; conservWeeks < 2
    r = assess({**_base(), "ctFractureLine": True, "fractureAgeWeeks": "5", "vasScore": "2",
                "conservativeWeeks": "1"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Conservative Therapy"
    assert r["recommendation"] == "Continue Conservative Therapy — Augmentation Premature"


def test_class_iib_insufficient_criteria():
    # imaging present, conservWeeks >= 2, but vas < 4 -> falls to else
    r = assess({**_base(), "ctFractureLine": True, "fractureAgeWeeks": "5", "vasScore": "2",
                "conservativeWeeks": "3"})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert r["recommendation"] == "Insufficient Criteria for Vertebral Augmentation"
    assert any("Complete ≥6-week conservative therapy trial" in s for s in r["optimizationSteps"])


def test_posterior_wall_compromise_and_height_loss_and_radiculopathy():
    r = assess({**_base(), "mriEdema": True, "fractureAgeWeeks": "3", "vasScore": "6",
                "osteoporosis": True, "posteriorWallIntact": False,
                "heightLoss": "60", "radiculopathy": True, "conservativeWeeks": "3"})
    # posteriorWallIntact False -> not Class I; mriEdema present, fractureWeeks<=12 but
    # posteriorWallIntact False -> not IIa either; falls to else (Insufficient Criteria)
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert any("Posterior vertebral wall compromise" in s for s in r["rationale"])
    assert any("Severe vertebral height loss (60%)" in s for s in r["rationale"])
    assert any("Radiculopathy present" in s for s in r["optimizationSteps"])


def test_procedure_note_kyphoplasty():
    r = assess({**_base(), "procedureType": "kyphoplasty"})
    assert r["procedureNote"].startswith("Kyphoplasty (balloon-assisted)")


def test_procedure_note_vertebroplasty():
    r = assess({**_base(), "procedureType": "vertebroplasty"})
    assert r["procedureNote"].startswith("Vertebroplasty: Direct cement injection")


def test_procedure_note_default():
    r = assess({**_base(), "procedureType": ""})
    assert r["procedureNote"].startswith("Both vertebroplasty and kyphoplasty")
