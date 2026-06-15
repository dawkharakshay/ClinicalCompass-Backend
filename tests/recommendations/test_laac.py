"""Tests for the LAAC / Watchman port.

No TypeScript oracle test existed for laacLogic.ts, so these fixtures are
derived directly from the TS branches in calculateLAACScore, covering each
major scoring/decision path plus the absolute-contraindication path.
"""

from app.recommendations.modules.laac import assess


def _base():
    """Minimal input — all booleans falsy, no anatomy contribution."""
    return {
        "sex": "male",
        "afType": "paroxysmal",
        "laaMorphology": "unknown",
        "laaSizeOstium": 0,
        "ckdStage": 0,
    }


def test_thrombus_absolute_contraindication():
    d = _base()
    d["laaThrombus"] = True
    # even with strong indications, thrombus short-circuits everything
    d["acContradicated"] = True
    d["chf"] = True
    d["hypertension"] = True
    d["stroke"] = True
    r = assess(d)
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Recommended"
    assert r["guidelineClass"] == "Class III: Harm"
    assert r["deviceConsideration"] == "Defer until thrombus resolves"
    assert r["references"] == []
    assert r["keyFindings"] == []
    assert any("LAA thrombus present" in w for w in r["warnings"])
    # scores are still reported
    assert r["cha2ds2vascScore"] == 4  # chf1 + htn1 + stroke2
    assert r["hasbledScore"] == 0


def test_appropriate_high_score():
    # CHA2DS2-VASc >=4 (+30), acContradicated (+30), HAS-BLED>=3 (+10),
    # ostium in range (+10) => 80 -> Appropriate
    d = _base()
    d["chf"] = True            # +1
    d["hypertension"] = True   # +1
    d["age75orOlder"] = True   # +2  => CHA2DS2 = 4
    d["acContradicated"] = True
    d["uncontrolledHypertension"] = True  # hasbled +1
    d["renalDisease"] = True              # +1
    d["liverDisease"] = True              # +1  => hasbled 3
    d["laaSizeOstium"] = 24
    r = assess(d)
    assert r["cha2ds2vascScore"] == 4
    assert r["hasbledScore"] == 3
    assert r["candidacyScore"] == 80
    assert r["recommendation"] == "Appropriate"
    assert r["guidelineClass"].startswith("Class IIa")
    assert "Watchman FLX (17–31 mm)" in r["deviceConsideration"]
    assert any("within Watchman FLX sizing range" in k for k in r["keyFindings"])
    assert len(r["references"]) == 5


def test_reasonable_score():
    # CHA2DS2 moderate (>=2 -> +20), intracranialHemorrhage (+25) => 45 -> Reasonable
    d = _base()
    d["chf"] = True          # +1
    d["diabetes"] = True     # +1  => CHA2DS2 = 2
    d["intracranialHemorrhage"] = True
    r = assess(d)
    assert r["cha2ds2vascScore"] == 2
    assert r["candidacyScore"] == 45
    assert r["recommendation"] == "Reasonable"
    assert r["guidelineClass"].startswith("Class IIb")


def test_consider_with_caution_score():
    # CHA2DS2 moderate (+20), no OAC contraindication branch (+5) => 25
    d = _base()
    d["chf"] = True
    d["diabetes"] = True  # CHA2DS2 = 2 -> +20
    r = assess(d)
    assert r["cha2ds2vascScore"] == 2
    assert r["candidacyScore"] == 25
    assert r["recommendation"] == "Consider with Caution"
    assert any("No OAC contraindication" in k for k in r["keyFindings"])


def test_not_recommended_low_stroke_risk():
    # CHA2DS2 < 2 => warning + (-10), then +5 (no OAC contra) => clamped to 0
    d = _base()
    r = assess(d)
    assert r["cha2ds2vascScore"] == 0
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Recommended"
    assert r["guidelineClass"].startswith("Class III")
    assert any("Low stroke risk" in w for w in r["warnings"])


def test_oversized_ostium_warning_and_penalty():
    # CHA2DS2 >=4 (+30), acFailed (+20), ostium 33 (>31 -> -5) => 45
    d = _base()
    d["stroke"] = True        # +2
    d["age75orOlder"] = True  # +2 => 4
    d["acFailed"] = True
    d["laaSizeOstium"] = 33
    r = assess(d)
    assert r["candidacyScore"] == 45
    assert any("exceeds Watchman FLX range" in w for w in r["warnings"])
    assert any("33 mm" in w for w in r["warnings"])


def test_undersized_ostium_warning():
    d = _base()
    d["stroke"] = True        # +2
    d["age75orOlder"] = True  # +2
    d["acContradicated"] = True
    d["laaSizeOstium"] = 14   # <17 and >0 -> -5
    r = assess(d)
    assert any("below minimum device size" in w for w in r["warnings"])


def test_cauliflower_and_esrd_and_ckd_warnings():
    d = _base()
    d["stroke"] = True
    d["age75orOlder"] = True
    d["acContradicated"] = True
    d["laaMorphology"] = "cauliflower"
    d["esrd"] = True
    d["ckdStage"] = 4
    d["pericardialDisease"] = True
    r = assess(d)
    assert any("Cauliflower LAA morphology" in w for w in r["warnings"])
    assert any("ESRD on dialysis" in w for w in r["warnings"])
    assert any("Advanced CKD" in w for w in r["warnings"])
    assert any("Pericardial disease" in w for w in r["warnings"])


def test_chicken_wing_keyfinding():
    d = _base()
    d["stroke"] = True
    d["age75orOlder"] = True
    d["acContradicated"] = True
    d["laaMorphology"] = "chicken-wing"
    r = assess(d)
    assert any("Chicken-wing LAA morphology" in k for k in r["keyFindings"])


def test_female_sex_and_acintolerant_and_gi_fall():
    # female (+1) chf(+1) htn(+1) => CHA2DS2 = 3 -> moderate +20
    # acIntolerant +15, gi_bleeding +10, fallRisk +5, ostium 20 +10 => 60 -> Appropriate
    d = _base()
    d["sex"] = "female"
    d["chf"] = True
    d["hypertension"] = True
    d["acIntolerant"] = True
    d["gi_bleeding"] = True
    d["fallRisk"] = True
    d["laaSizeOstium"] = 20
    r = assess(d)
    assert r["cha2ds2vascScore"] == 3
    assert r["candidacyScore"] == 60
    assert r["recommendation"] == "Appropriate"


def test_hasbled_capped_at_9():
    d = _base()
    for f in [
        "uncontrolledHypertension", "renalDisease", "liverDisease",
        "priorStrokeHistory", "priorMajorBleeding", "labileINR",
        "elderlyAge65", "drugsAlcohol",
    ]:
        d[f] = True
    r = assess(d)
    # only 8 components exist, so max is 8 (min(8,9))
    assert r["hasbledScore"] == 8
