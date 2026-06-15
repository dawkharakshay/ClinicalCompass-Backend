"""Tests for the Renal Cryoablation Clinical Compass port.

Fixtures derived 1:1 from the TypeScript branches in
old_static_code/client/src/lib/renalCryoablationLogic.ts
(no TS test file exists for this module).
"""

from app.recommendations.modules.renalcryoablation import assess


def _base(**overrides):
    data = {
        "tumorSizeCm": 3,
        "tumorLocation": "exophytic",
        "renalNephrometryScore": 6,
        "contralateralKidneyFunction": "normal",
        "patientAge": 60,
        "performanceStatus": "0",
        "priorNephrectomy": False,
        "hereditarySyndrome": False,
        "multipleIpsilateralTumors": False,
        "comorbidities": {
            "ckd": False,
            "diabetes": False,
            "hypertension": False,
            "cardiopulmonaryDisease": False,
            "anticoagulation": False,
        },
        "biopsyPerformed": True,
        "biopsyResult": "rcc_clear_cell",
        "priorAblation": False,
        "imagingModality": "ct",
        "bosnakCategory": "solid",
    }
    data.update(overrides)
    return data


def test_t1a_low_complexity_indicated():
    res = assess(_base(tumorSizeCm=3, renalNephrometryScore=6))
    assert res["recommendation"] == "indicated"
    assert res["cor"] == "I"
    assert res["loe"] == "B"
    assert "INDICATED" in res["summary"]
    assert "this 3 cm T1a renal mass" in res["summary"]
    assert "low complexity" in res["summary"]
    assert len(res["rationale"]) == 2


def test_t1a_intermediate_indicated():
    res = assess(_base(tumorSizeCm=4, renalNephrometryScore=9))
    assert res["recommendation"] == "indicated"
    assert res["cor"] == "I"
    assert res["loe"] == "B"
    assert "intermediate complexity" in res["summary"]


def test_t1a_high_complexity_consider():
    res = assess(_base(tumorSizeCm=4, renalNephrometryScore=10))
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIa"
    assert res["loe"] == "B"
    assert "MAY BE CONSIDERED" in res["summary"]
    # high RENAL score triggers technical consideration
    assert any("High R.E.N.A.L." in t for t in res["technicalConsiderations"])


def test_t1b_high_surgical_risk_age():
    res = assess(_base(tumorSizeCm=5, renalNephrometryScore=8, patientAge=72))
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIa"
    assert res["loe"] == "B-NR"
    assert len(res["rationale"]) == 2


def test_t1b_surgically_fit_consider_iib():
    res = assess(_base(tumorSizeCm=5, renalNephrometryScore=8, patientAge=55))
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIb"
    assert res["loe"] == "B-NR"
    assert any(
        "preferred treatment for T1b tumors" in w for w in res["warnings"]
    )


def test_t1b_cardiopulmonary_high_risk():
    res = assess(
        _base(
            tumorSizeCm=6,
            renalNephrometryScore=7,
            patientAge=50,
            comorbidities={
                "ckd": False,
                "diabetes": False,
                "hypertension": False,
                "cardiopulmonaryDisease": True,
                "anticoagulation": False,
            },
        )
    )
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIa"


def test_t2_not_indicated():
    res = assess(_base(tumorSizeCm=8, renalNephrometryScore=8))
    assert res["recommendation"] == "not_indicated"
    assert res["cor"] == "III"
    assert res["loe"] == "B-NR"
    assert "NOT RECOMMENDED" in res["summary"]
    assert any("outside standard ablation criteria" in w for w in res["warnings"])


def test_hereditary_upgrades_consider_to_indicated():
    # T1a high complexity -> consider, hereditary upgrades to indicated
    res = assess(
        _base(tumorSizeCm=4, renalNephrometryScore=11, hereditarySyndrome=True)
    )
    assert res["recommendation"] == "indicated"
    # cor remains IIa (only recommendation is upgraded)
    assert res["cor"] == "IIa"
    assert any("Hereditary renal cell carcinoma" in r for r in res["rationale"])


def test_hereditary_not_applied_to_t2():
    res = assess(_base(tumorSizeCm=9, renalNephrometryScore=8, hereditarySyndrome=True))
    assert res["recommendation"] == "not_indicated"
    assert not any("Hereditary renal cell" in r for r in res["rationale"])


def test_solitary_kidney_upgrades_t1b_from_not_indicated():
    # T2 would be not_indicated, but only T1b is upgraded by solitary branch.
    # Use a T1b that is surgically fit but solitary -> already consider; check rationale.
    res = assess(
        _base(
            tumorSizeCm=5,
            renalNephrometryScore=7,
            patientAge=55,
            contralateralKidneyFunction="solitary",
        )
    )
    # contralateral != normal => T1b high-risk branch -> consider IIa
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIa"
    assert any("Solitary kidney or CKD" in r for r in res["rationale"])
    assert any("renal function monitoring" in w for w in res["warnings"])


def test_ckd_adds_rationale_and_warning():
    res = assess(
        _base(
            tumorSizeCm=3,
            renalNephrometryScore=5,
            comorbidities={
                "ckd": True,
                "diabetes": False,
                "hypertension": False,
                "cardiopulmonaryDisease": False,
                "anticoagulation": False,
            },
        )
    )
    assert res["recommendation"] == "indicated"
    assert any("Solitary kidney or CKD" in r for r in res["rationale"])


def test_anticoagulation_warning():
    res = assess(
        _base(
            comorbidities={
                "ckd": False,
                "diabetes": False,
                "hypertension": False,
                "cardiopulmonaryDisease": False,
                "anticoagulation": True,
            }
        )
    )
    assert any("anticoagulation therapy" in w for w in res["warnings"])


def test_no_biopsy_warning():
    res = assess(_base(biopsyPerformed=False))
    assert any("Pre-ablation biopsy has not been performed" in w for w in res["warnings"])


def test_benign_biopsy_downgrades_to_consider():
    res = assess(_base(biopsyResult="oncocytoma"))
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIb"
    assert any("benign lesion" in w for w in res["warnings"])
    assert any("Biopsy result: oncocytoma" in w for w in res["warnings"])


def test_angiomyolipoma_benign():
    res = assess(_base(biopsyResult="angiomyolipoma"))
    assert res["recommendation"] == "consider"
    assert res["cor"] == "IIb"
    assert any("Biopsy result: angiomyolipoma" in w for w in res["warnings"])


def test_indeterminate_biopsy_warning():
    res = assess(_base(biopsyResult="indeterminate"))
    assert any("Indeterminate biopsy result" in w for w in res["warnings"])
    # recommendation unchanged from base indicated
    assert res["recommendation"] == "indicated"


def test_prior_ablation_rationale():
    res = assess(_base(priorAblation=True))
    assert any("Prior ablation" in r for r in res["rationale"])


def test_hilar_technical_consideration():
    res = assess(_base(tumorLocation="hilar"))
    assert any("Hilar tumor location" in t for t in res["technicalConsiderations"])


def test_endophytic_technical_consideration():
    res = assess(_base(tumorLocation="endophytic"))
    assert any("Endophytic tumor" in t for t in res["technicalConsiderations"])


def test_ultrasound_technical_consideration():
    res = assess(_base(imagingModality="ultrasound"))
    assert any("Ultrasound guidance" in t for t in res["technicalConsiderations"])


def test_diabetes_technical_consideration():
    res = assess(
        _base(
            comorbidities={
                "ckd": False,
                "diabetes": True,
                "hypertension": False,
                "cardiopulmonaryDisease": False,
                "anticoagulation": False,
            }
        )
    )
    assert any("Diabetes mellitus" in t for t in res["technicalConsiderations"])


def test_multiple_ipsilateral_rationale():
    res = assess(_base(multipleIpsilateralTumors=True))
    assert any("Multiple ipsilateral renal tumors" in r for r in res["rationale"])


def test_references_present():
    res = assess(_base())
    assert len(res["references"]) == 8
    assert res["references"][0].startswith("Campbell S")


def test_decimal_size_formatting():
    res = assess(_base(tumorSizeCm=3.5, renalNephrometryScore=6))
    assert "this 3.5 cm T1a renal mass" in res["summary"]
    assert "score 6" in res["summary"]
