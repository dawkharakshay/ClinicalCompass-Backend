"""Tests for the AF Ablation port.

Fixtures are derived directly from the TS branches in
old_static_code/client/src/lib/afAblationLogic.ts (no oracle .test.ts exists),
covering each major decision path plus the contraindication early-return.
"""

from app.recommendations.modules.afablation import assess


def _base(**overrides):
    data = {
        "age": 60,
        "sex": "male",
        "afType": "paroxysmal",
        "afDuration": 6,
        "symptomBurden": "severe",
        "chf": False,
        "hypertension": False,
        "age75orOlder": False,
        "diabetes": False,
        "stroke": False,
        "vascularDisease": False,
        "age65to74": False,
        "aadFailed": False,
        "aadIntolerant": False,
        "aadTrialed": [],
        "lvef": 60,
        "laSize": 40,
        "structuralHeartDisease": False,
        "hcm": False,
        "sleepApnea": False,
        "sleepApneaTreated": False,
        "obesity": False,
        "bmi": 25,
        "thyroidDisease": False,
        "thyroidTreated": False,
        "ckdStage": 0,
        "onAnticoagulation": False,
        "anticoagulantType": "none",
        "activeInfection": False,
        "recentThrombus": False,
        "uncontrolledHF": False,
        "severeMitralStenosis": False,
    }
    data.update(overrides)
    return data


def test_laa_thrombus_contraindication_early_return():
    # chf + hypertension => CHA2DS2-VASc 2
    r = assess(_base(recentThrombus=True, chf=True, hypertension=True))
    assert r["candidacyScore"] == 0
    assert r["cha2ds2vascScore"] == 2
    assert r["recommendation"] == "Not Recommended"
    assert r["guidelineClass"] == "Class III: Harm"
    assert r["preferredApproach"] == (
        "Anticoagulate for ≥3 weeks and repeat TEE before reconsidering ablation"
    )
    assert r["anticoagulationNote"] == "Anticoagulation required; repeat TEE in 3–6 weeks"
    assert r["references"] == []
    assert r["keyFindings"] == []
    assert any("LAA thrombus" in w for w in r["warnings"])


def test_strongly_recommended_paroxysmal_severe_aadfailed():
    # paroxysmal 25 + severe 25 + aadFailed 20 + laSize<=45 5 + lvef<35 10 = 85
    r = assess(_base(aadFailed=True, aadTrialed=["flecainide", "sotalol"], lvef=30))
    assert r["candidacyScore"] == 85
    assert r["recommendation"] == "Strongly Recommended"
    assert r["guidelineClass"] == "Class I: Catheter ablation is recommended"
    assert r["cha2ds2vascScore"] == 0
    assert any(
        "Failed AAD therapy (flecainide, sotalol)" in f for f in r["keyFindings"]
    )
    assert any("LA size 40 mm" in f for f in r["keyFindings"])
    assert any("Reduced LVEF (30%)" in f for f in r["keyFindings"])
    # CHA2DS2-VASc 0 => not routinely recommended note
    assert "not routinely recommended" in r["anticoagulationNote"]


def test_recommended_class_iia():
    # persistent 20 + moderate 15 + no AAD 5 + laSize<=45 5 = 45
    r = assess(_base(afType="persistent", symptomBurden="moderate", lvef=60))
    assert r["candidacyScore"] == 45
    assert r["recommendation"] == "Recommended"
    assert r["guidelineClass"] == "Class IIa: Catheter ablation is reasonable"


def test_reasonable_class_iib():
    # longstanding-persistent 10 + mild 5 + aadIntolerant 15 + laSize<=45 5 = 35
    r = assess(
        _base(
            afType="longstanding-persistent",
            symptomBurden="mild",
            aadIntolerant=True,
            lvef=60,
        )
    )
    assert r["candidacyScore"] == 35
    assert r["recommendation"] == "Reasonable"
    assert r["guidelineClass"] == "Class IIb: Catheter ablation may be considered"
    assert any("Long-standing persistent AF" in w for w in r["warnings"])


def test_not_recommended_permanent_asymptomatic():
    # permanent -20 + asymptomatic(none) -10 + no AAD +5 + laSize<=45 +5 = -20 -> clamp 0
    r = assess(_base(afType="permanent", symptomBurden="none", lvef=60))
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Recommended"
    assert r["guidelineClass"] == "Class III: Ablation not recommended in current clinical context"
    assert any("Permanent AF" in w for w in r["warnings"])
    assert any("Asymptomatic AF" in w for w in r["warnings"])


def test_cha2ds2vasc_score_one_male_class_iib_note():
    # single chf => score 1, male => Class IIb anticoag note
    r = assess(_base(chf=True))
    assert r["cha2ds2vascScore"] == 1
    assert "anticoagulation may be considered (Class IIb)" in r["anticoagulationNote"]


def test_cha2ds2vasc_female_adds_point_and_score_two_note():
    # female adds 1; chf adds 1 => 2 => Class I anticoag note
    r = assess(_base(sex="female", chf=True))
    assert r["cha2ds2vascScore"] == 2
    assert "long-term anticoagulation recommended" in r["anticoagulationNote"]


def test_modifiable_risk_factors_and_anticoag_warning():
    # paroxysmal 25 + severe 25 + no AAD 5 + LA>55 -15 + OSA -5 + obesity -5 + thyroid -10
    # = 20 ; lvef 60 no bonus
    r = assess(
        _base(
            laSize=60,
            sleepApnea=True,
            sleepApneaTreated=False,
            obesity=True,
            bmi=38,
            thyroidDisease=True,
            thyroidTreated=False,
            chf=True,
            hypertension=True,
            onAnticoagulation=False,
        )
    )
    assert r["candidacyScore"] == 20
    assert r["recommendation"] == "Not Recommended"
    assert any("Markedly enlarged LA (60 mm)" in w for w in r["warnings"])
    assert any("Untreated obstructive sleep apnea" in w for w in r["warnings"])
    assert any("BMI 38" in w for w in r["warnings"])
    assert any("Untreated thyroid disease" in w for w in r["warnings"])
    assert any("anticoagulation required; start before ablation" in w for w in r["warnings"])


def test_enlarged_la_moderate_branch():
    r = assess(_base(laSize=50))
    assert any("Enlarged LA (50 mm)" in w for w in r["warnings"])
