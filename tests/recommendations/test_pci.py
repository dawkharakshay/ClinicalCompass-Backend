"""Oracle tests for the Elective PCI Clinical Compass port.

No TS test exists for pciLogic.ts; fixtures are derived from the TS branches
(calculatePCIScore) covering each major decision path plus an
edge/contraindication path. Scores are hand-computed from the TS deltas.
"""

from __future__ import annotations

from app.recommendations.modules.pci import assess


def _base() -> dict:
    """A neutral, on-OMT, DAPT-tolerant patient with no findings (score 0)."""
    return {
        "age": 65,
        "sex": "male",
        "diabetesMellitus": False,
        "ccsAngina": 0,
        "dyspnea": False,
        "silentIschemia": False,
        "syntaxScore": 10,
        "numVesselsDisease": 1,
        "leftMainDisease": False,
        "proximalLadDisease": False,
        "chronicTotalOcclusion": False,
        "lvef": 60,
        "ffrPositive": False,
        "stressTestPositive": False,
        "stressTestHighRisk": False,
        "optimalMedicalTherapy": True,
        "omtDuration": 6,
        "priorCABG": False,
        "ckdStage": 0,
        "bleedingRisk": "low",
        "contrastAllergy": False,
        "daptTolerance": True,
    }


def test_syntax_categorization_boundaries():
    assert assess({**_base(), "syntaxScore": 22})["syntaxCategory"] == "Low"
    assert assess({**_base(), "syntaxScore": 23})["syntaxCategory"] == "Intermediate"
    assert assess({**_base(), "syntaxScore": 32})["syntaxCategory"] == "Intermediate"
    assert assess({**_base(), "syntaxScore": 33})["syntaxCategory"] == "High"


def test_appropriate_high_score():
    # +30 highRisk, +20 ffr, +20 ccs>=3, +10 proximalLAD = 80
    data = {
        **_base(),
        "stressTestHighRisk": True,
        "ffrPositive": True,
        "ccsAngina": 3,
        "proximalLadDisease": True,
        "syntaxScore": 10,
        "numVesselsDisease": 1,
    }
    r = assess(data)
    assert r["candidacyScore"] == 80
    assert r["recommendation"] == "Appropriate"
    assert r["syntaxCategory"] == "Low"
    assert (
        r["preferredStrategy"]
        == "Single-vessel or low-complexity PCI with drug-eluting stent (DES)"
    )
    assert (
        "Severe angina (CCS Class 3) refractory to medical therapy"
        in r["keyFindings"]
    )
    assert (
        "Symptoms persist despite 6 months of optimal medical therapy"
        in r["keyFindings"]
    )
    assert r["warnings"] == []


def test_appropriate_multivessel_strategy():
    # Force score >=60 with numVessels != 1 and syntaxCategory != Low.
    # +30 highRisk, +20 ffr, +20 ccs>=3, +15 leftMain(intermediate) = 85
    data = {
        **_base(),
        "stressTestHighRisk": True,
        "ffrPositive": True,
        "ccsAngina": 4,
        "leftMainDisease": True,
        "syntaxScore": 30,  # Intermediate
        "numVesselsDisease": 2,
    }
    r = assess(data)
    assert r["candidacyScore"] == 85
    assert r["recommendation"] == "Appropriate"
    assert (
        r["preferredStrategy"]
        == "Heart Team discussion; PCI feasible for low/intermediate SYNTAX anatomy"
    )


def test_may_be_appropriate():
    # +15 stressPos, +10 ccs=2, +15 leftMain(intermediate) = 40
    data = {
        **_base(),
        "stressTestPositive": True,
        "ccsAngina": 2,
        "leftMainDisease": True,
        "syntaxScore": 30,  # Intermediate
        "numVesselsDisease": 2,
        "omtDuration": 2,  # < 3 -> no persistence finding
    }
    r = assess(data)
    assert r["candidacyScore"] == 40
    assert r["recommendation"] == "May Be Appropriate"
    assert (
        r["appropriatenessRating"]
        == "Score 4–6: Elective PCI may be appropriate; individualized decision required"
    )
    assert (
        r["preferredStrategy"]
        == "Heart Team evaluation recommended; consider ISCHEMIA trial data for stable CAD"
    )
    assert "Positive stress test with moderate ischemia" in r["keyFindings"]
    assert "Symptomatic angina (CCS Class 2)" in r["keyFindings"]


def test_rarely_appropriate_not_on_omt():
    # not OMT (-15), no positive findings -> clamp 0
    data = {
        **_base(),
        "optimalMedicalTherapy": False,
        "omtDuration": 0,
    }
    r = assess(data)
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Rarely Appropriate"
    assert (
        "Patient not on optimal medical therapy — OMT trial recommended "
        "before elective PCI per ISCHEMIA trial" in r["warnings"]
    )
    assert (
        r["preferredStrategy"]
        == "Optimize medical therapy; reassess symptoms at 3–6 months; "
        "consider CABG if anatomy favors"
    )


def test_contraindication_edge_dapt_and_high_syntax():
    # leftMain+High (-10), 3-vessel+High (-15), daptIntolerant (-20),
    # bleeding high (-5), not OMT (-15) -> negative, clamp 0
    data = {
        **_base(),
        "leftMainDisease": True,
        "numVesselsDisease": 3,
        "syntaxScore": 40,  # High
        "daptTolerance": False,
        "bleedingRisk": "high",
        "ckdStage": 5,
        "lvef": 30,
        "optimalMedicalTherapy": False,
    }
    r = assess(data)
    assert r["candidacyScore"] == 0
    assert r["recommendation"] == "Rarely Appropriate"
    assert r["syntaxCategory"] == "High"
    w = r["warnings"]
    assert (
        "Left main disease with high SYNTAX score — CABG preferred (Class I)" in w
    )
    assert (
        "3-vessel disease with high SYNTAX score — CABG preferred over PCI (Class I)"
        in w
    )
    assert (
        "Unable to tolerate DAPT — high stent thrombosis risk; consider "
        "CABG or medical therapy" in w
    )
    assert (
        "High bleeding risk — consider bare-metal stent or short DAPT duration strategy"
        in w
    )
    assert (
        "Advanced CKD (Stage ≥4) — contrast nephropathy risk; "
        "pre-hydration and iso-osmolar contrast required" in w
    )
    assert (
        "Severely reduced LVEF (<35%) — consider hemodynamic support and "
        "Heart Team evaluation" in w
    )


def test_three_vessel_intermediate_syntax_warning():
    data = {
        **_base(),
        "numVesselsDisease": 3,
        "syntaxScore": 30,  # Intermediate
    }
    r = assess(data)
    assert (
        "3-vessel disease with intermediate SYNTAX score — Heart Team discussion recommended"
        in r["warnings"]
    )


def test_lvef_reduced_adds_score_and_finding():
    data = {**_base(), "lvef": 40}
    r = assess(data)
    assert r["candidacyScore"] == 5
    assert (
        "Reduced LVEF (40%) — revascularization may improve function if "
        "viable myocardium present" in r["keyFindings"]
    )


def test_string_inputs_coerced():
    # Form fields arrive as strings; ensure numeric coercion matches.
    data = {
        **_base(),
        "syntaxScore": "10",
        "ccsAngina": "3",
        "numVesselsDisease": "1",
        "lvef": "60",
        "omtDuration": "6",
        "stressTestHighRisk": True,
        "ffrPositive": True,
        "proximalLadDisease": True,
    }
    r = assess(data)
    assert r["candidacyScore"] == 80
    assert r["recommendation"] == "Appropriate"


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 5
    assert r["references"][0].startswith("Lawton JS")
