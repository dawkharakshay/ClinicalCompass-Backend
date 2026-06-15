"""Cholecystectomy engine — fixtures derived directly from cholecystectomyLogic.ts branches."""

from app.recommendations.modules.cholecystectomy import assess


def _base() -> dict:
    return {
        "age": "50",
        "sex": "female",
        "indication": "symptomatic-cholelithiasis",
        "biliaryColic": False,
        "frequency": "rare",
        "painDuration": "0",
        "nausea": False,
        "intolerance": False,
        "ultrasoundConfirmed": False,
        "gallstonesPresent": False,
        "polypSize": "0",
        "wallThickening": False,
        "pericholecysticFluid": False,
        "ejectionFraction": "60",
        "acuteCholecystitis": False,
        "choledocholithiasis": False,
        "cholangitis": False,
        "gallstonePancreatitis": False,
        "mirizzySyndrome": False,
        "asa": "2",
        "priorAbdominalSurgery": False,
        "cirrhosis": False,
        "coagulopathy": False,
        "pregnancy": False,
        "pregnancyTrimester": "0",
        "triedDietModification": False,
        "triedMedications": False,
    }


def test_baseline_not_indicated():
    r = assess(_base())
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Not Indicated"
    assert r["urgency"] == "Elective"
    assert r["approach"] == "Conservative management; dietary modification; reassess in 3–6 months"
    assert r["keyFindings"] == []
    assert r["warnings"] == []
    assert len(r["references"]) == 4


def test_acute_cholecystitis_semiurgent():
    # acute (40) -> score 40 -> Indicated, Semi-urgent
    r = assess({**_base(), "acuteCholecystitis": True})
    assert r["candidacyScore"] == 40
    assert r["recommendation"] == "Indicated"
    assert r["urgency"] == "Semi-urgent (within 6 weeks)"
    assert any("Acute cholecystitis" in f for f in r["keyFindings"])


def test_acute_cholangitis_urgent_warning():
    r = assess({**_base(), "acuteCholecystitis": True, "cholangitis": True})
    assert r["urgency"] == "Urgent (within 72 hours)"
    assert any("Acute cholangitis" in w for w in r["warnings"])


def test_gallstone_pancreatitis():
    r = assess({**_base(), "gallstonePancreatitis": True})
    assert r["candidacyScore"] == 40
    assert r["urgency"] == "Semi-urgent (within 6 weeks)"
    assert any("Gallstone pancreatitis" in f for f in r["keyFindings"])


def test_symptomatic_cholelithiasis_strongly_indicated():
    # biliaryColic + gallstones (30) + daily (15) + painDuration>=3 (10) = 55 -> Indicated
    r = assess({
        **_base(),
        "biliaryColic": True,
        "gallstonesPresent": True,
        "frequency": "daily",
        "painDuration": "6",
    })
    assert r["candidacyScore"] == 55
    assert r["recommendation"] == "Indicated"
    assert any("Symptomatic cholelithiasis" in f for f in r["keyFindings"])
    assert any("Daily biliary colic" in f for f in r["keyFindings"])
    assert any("6 months" in f for f in r["keyFindings"])


def test_frequency_weekly_monthly():
    assert assess({**_base(), "frequency": "weekly"})["candidacyScore"] == 10
    assert assess({**_base(), "frequency": "monthly"})["candidacyScore"] == 5


def test_biliary_dyskinesia_low_ef():
    # dyskinesia + EF<35 (25) -> Consider (>=15)
    r = assess({
        **_base(),
        "indication": "biliary-dyskinesia",
        "ejectionFraction": "20",
    })
    assert r["candidacyScore"] == 25
    assert r["recommendation"] == "Consider"
    assert any("ejection fraction 20%" in f for f in r["keyFindings"])


def test_biliary_dyskinesia_normal_ef_no_points():
    r = assess({
        **_base(),
        "indication": "biliary-dyskinesia",
        "ejectionFraction": "50",
    })
    assert r["candidacyScore"] == 0


def test_polyp_large():
    # polyp >=10 (35) -> Indicated
    r = assess({**_base(), "indication": "polyp", "polypSize": "12"})
    assert r["candidacyScore"] == 35
    assert r["recommendation"] == "Indicated"
    assert any("≥10mm" in f for f in r["keyFindings"])


def test_polyp_intermediate():
    # polyp 6-9 (15) -> Consider
    r = assess({**_base(), "indication": "polyp", "polypSize": "7"})
    assert r["candidacyScore"] == 15
    assert r["recommendation"] == "Consider"
    assert any("7mm" in f for f in r["keyFindings"])


def test_polyp_small_no_points():
    r = assess({**_base(), "indication": "polyp", "polypSize": "4"})
    assert r["candidacyScore"] == 0


def test_choledocholithiasis_and_wall_thickening():
    # choledoch (20) + wall (10) = 30 -> Consider
    r = assess({**_base(), "choledocholithiasis": True, "wallThickening": True})
    assert r["candidacyScore"] == 30
    assert r["recommendation"] == "Consider"


def test_asa4_penalty():
    # acute (40) - asa4 (15) = 25 -> Consider, plus warning
    r = assess({**_base(), "acuteCholecystitis": True, "asa": "4"})
    assert r["candidacyScore"] == 25
    assert r["recommendation"] == "Consider"
    assert any("ASA Class IV" in w for w in r["warnings"])


def test_asa3_warning_no_penalty():
    r = assess({**_base(), "acuteCholecystitis": True, "asa": "3"})
    assert r["candidacyScore"] == 40
    assert any("ASA Class III" in w for w in r["warnings"])


def test_cirrhosis_penalty_and_approach():
    # acute(40)+choledoch(20)+wall(10) = 70 - cirrhosis(10) = 60 -> Strongly Indicated
    r = assess({
        **_base(),
        "acuteCholecystitis": True,
        "choledocholithiasis": True,
        "wallThickening": True,
        "cirrhosis": True,
    })
    assert r["candidacyScore"] == 60
    assert r["recommendation"] == "Strongly Indicated"
    assert r["approach"].startswith(
        "Laparoscopic cholecystectomy — experienced hepatobiliary surgeon"
    )
    assert any("Cirrhosis" in w for w in r["warnings"])


def test_strongly_indicated_standard_approach():
    # acute(40)+choledoch(20)+wall(10) = 70 -> Strongly Indicated, standard approach
    r = assess({
        **_base(),
        "acuteCholecystitis": True,
        "choledocholithiasis": True,
        "wallThickening": True,
    })
    assert r["candidacyScore"] == 70
    assert r["recommendation"] == "Strongly Indicated"
    assert "single-incision laparoscopic (SILC)" in r["approach"]


def test_pregnancy_trimester2_keyfinding():
    r = assess({**_base(), "pregnancy": True, "pregnancyTrimester": "2"})
    assert any("2nd trimester" in f for f in r["keyFindings"])


def test_pregnancy_trimester3_warning():
    r = assess({**_base(), "pregnancy": True, "pregnancyTrimester": "3"})
    assert any("3rd trimester" in w for w in r["warnings"])


def test_mirizzi_warning_and_approach():
    # large score to reach Strongly Indicated with mirizzi approach
    r = assess({
        **_base(),
        "acuteCholecystitis": True,
        "gallstonePancreatitis": True,
        "mirizzySyndrome": True,
    })
    assert r["candidacyScore"] == 80
    assert r["recommendation"] == "Strongly Indicated"
    assert r["approach"].startswith(
        "Laparoscopic cholecystectomy — experienced hepatobiliary surgeon"
    )
    assert any("Mirizzi syndrome" in w for w in r["warnings"])


def test_score_clamped_to_100():
    r = assess({
        **_base(),
        "acuteCholecystitis": True,        # 40
        "gallstonePancreatitis": True,     # 40
        "biliaryColic": True,
        "gallstonesPresent": True,         # 30
        "frequency": "daily",              # 15
        "painDuration": "12",              # 10
        "choledocholithiasis": True,       # 20
        "wallThickening": True,            # 10
        "triedDietModification": True,     # 5
    })
    assert r["candidacyScore"] == 100
