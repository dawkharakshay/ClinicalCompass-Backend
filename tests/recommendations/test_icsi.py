"""Oracle tests for the ICSI module.

No server-side *.test.ts exists for ICSI; fixtures are derived directly from
the TS `evaluate` branches in ICSICompass.tsx covering each decision path.
"""

from app.recommendations.modules.icsi import assess


def _base(**overrides):
    data = {
        "spermConcentration": "normal",
        "totalMotileCount": 0,
        "morphologyPercent": 4,  # normal morphology -> avoid relative trigger
        "priorIVFFailedFertilization": False,
        "priorIVFLowFertilization": False,
        "antispermAntibodies": False,
        "obstructiveAzoospermia": False,
        "nonObstructiveAzoospermia": False,
        "surgicalSpermRetrieval": False,
        "frozenSperm": False,
        "unexplainedIVFFailure": False,
    }
    data.update(overrides)
    return data


def test_absolute_severe_concentration():
    r = assess(_base(spermConcentration="severe"))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "ICSI — absolute indication"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("Severe male factor" in x for x in r["rationale"])


def test_absolute_azoospermia():
    r = assess(_base(spermConcentration="azoospermia"))
    assert r["recommendation"] == "indicated"
    assert any("Severe male factor" in x for x in r["rationale"])


def test_absolute_surgical_retrieval_rationale():
    r = assess(_base(surgicalSpermRetrieval=True))
    assert r["recommendation"] == "indicated"
    assert r["rationale"][0].startswith("Surgical sperm retrieval:")


def test_absolute_obstructive_and_nonobstructive():
    r = assess(_base(obstructiveAzoospermia=True, nonObstructiveAzoospermia=True))
    assert r["recommendation"] == "indicated"
    assert any("Surgical sperm retrieval" in x for x in r["rationale"])


def test_absolute_prior_failed_fertilization():
    r = assess(_base(priorIVFFailedFertilization=True))
    assert r["recommendation"] == "indicated"
    assert any("Prior IVF with failed fertilization" in x for x in r["rationale"])


def test_absolute_antisperm_antibodies():
    r = assess(_base(antispermAntibodies=True))
    assert r["recommendation"] == "indicated"
    assert any("Antisperm antibodies" in x for x in r["rationale"])


def test_absolute_combination_multiple_rationale():
    r = assess(
        _base(
            spermConcentration="severe",
            surgicalSpermRetrieval=True,
            priorIVFFailedFertilization=True,
            antispermAntibodies=True,
        )
    )
    assert r["recommendation"] == "indicated"
    assert len(r["rationale"]) == 4


def test_relative_moderate_concentration():
    r = assess(_base(spermConcentration="moderate"))
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "ICSI — relative indication (shared decision-making)"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"
    assert len(r["warnings"]) == 1


def test_relative_low_fertilization():
    r = assess(_base(priorIVFLowFertilization=True))
    assert r["recommendation"] == "consider"


def test_relative_frozen_sperm():
    r = assess(_base(frozenSperm=True))
    assert r["recommendation"] == "consider"


def test_relative_unexplained_failure():
    r = assess(_base(unexplainedIVFFailure=True))
    assert r["recommendation"] == "consider"


def test_relative_low_morphology():
    r = assess(_base(morphologyPercent=3))
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIa"


def test_not_indicated_all_normal():
    r = assess(_base(morphologyPercent=4))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Conventional IVF insemination — ICSI not indicated"
    assert r["cor"] == "III"
    assert r["loe"] == "B"
    assert len(r["warnings"]) == 1


def test_default_morphology_zero_triggers_relative():
    # parseFloat("") || 0 => 0; 0 < 4 -> relative indication (TS faithful)
    r = assess(_base(morphologyPercent=0))
    assert r["recommendation"] == "consider"


def test_absolute_precedence_over_relative():
    # severe (absolute) wins even with relative morphology present
    r = assess(_base(spermConcentration="severe", morphologyPercent=2))
    assert r["recommendation"] == "indicated"


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 3
    assert r["references"][2].startswith("Palermo G")
