"""Tests for the Varicocelectomy Clinical Compass engine.

Fixtures authored from the inline evaluate() branches in
old_static_code/client/src/pages/VaricocelectomyCompass.tsx (no oracle test
file exists for this surgical-repair engine; varicocele.test.ts covers the
separate embolization engine).
"""

from app.recommendations.modules.varicocelectomy import assess


def _base(**overrides):
    """Mirror VaricocelectomyCompass defaultInputs, override per test."""
    data = {
        "grade": "II",
        "bilateral": False,
        "totalMotileCount": 0,
        "spermConcentration": 0,
        "progressiveMotility": 0,
        "morphologyKruger": 0,
        "fshLevel": 0,
        "testosteroneLevel": 0,
        "testisVolumeDiff": 0,
        "partnerAge": 0,
        "partnerFertilityNormal": True,
        "infertilityDuration": 0,
        "painPresent": False,
        "adolescent": False,
        "priorVaricocelectomy": False,
    }
    data.update(overrides)
    return data


def test_adolescent_with_significant_atrophy_indicated():
    r = assess(_base(adolescent=True, testisVolumeDiff=25))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Microsurgical Varicocelectomy"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"
    assert any("≥20%" in s for s in r["rationale"])


def test_adolescent_below_threshold_consider_observation():
    r = assess(_base(adolescent=True, testisVolumeDiff=10))
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "Observation with annual semen analysis"
    # cor/loe unchanged from defaults in this branch
    assert r["cor"] == "III"
    assert r["loe"] == "B"


def test_adolescent_takes_precedence_over_pain():
    # adolescent branch evaluated first even if pain present
    r = assess(_base(adolescent=True, testisVolumeDiff=30, painPresent=True))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Microsurgical Varicocelectomy"


def test_pain_indication_consider():
    # non-adolescent, palpable, pain present
    r = assess(
        _base(
            grade="III",
            painPresent=True,
            # normal semen so the fertility branch would not fire anyway,
            # but pain branch precedes it
            spermConcentration=20,
            progressiveMotility=40,
            morphologyKruger=5,
            totalMotileCount=10,
            infertilityDuration=24,
        )
    )
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "Microsurgical Varicocelectomy (pain indication)"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"


def test_fertility_indication_grade_a():
    r = assess(
        _base(
            grade="II",
            spermConcentration=10,  # abnormal (<15)
            progressiveMotility=40,
            morphologyKruger=5,
            totalMotileCount=10,
            infertilityDuration=12,
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Microsurgical Varicocelectomy (subinguinal approach preferred)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("Grade A" in s for s in r["rationale"])
    assert any("Baazeem 2011" in s for s in r["rationale"])


def test_fertility_not_indicated_when_infertility_under_12_months():
    r = assess(
        _base(
            grade="II",
            spermConcentration=10,  # abnormal
            infertilityDuration=6,
        )
    )
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Observation"


def test_subclinical_explicitly_not_indicated():
    r = assess(_base(grade="subclinical"))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "No repair — subclinical varicocele"
    assert r["cor"] == "III"
    assert r["loe"] == "A"
    assert any("should NOT be repaired" in w for w in r["warnings"])


def test_subclinical_with_abnormal_semen_still_not_indicated():
    # clinicallySignificant is False for subclinical, so fertility branch skipped
    r = assess(
        _base(
            grade="subclinical",
            spermConcentration=5,
            infertilityDuration=24,
        )
    )
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "No repair — subclinical varicocele"
    assert r["loe"] == "A"


def test_default_observation_branch():
    # palpable, but semen normal -> abnormalSemen False -> falls to else
    r = assess(
        _base(
            grade="II",
            spermConcentration=20,
            progressiveMotility=40,
            morphologyKruger=5,
            totalMotileCount=10,
            infertilityDuration=24,
        )
    )
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Observation"
    assert r["cor"] == "III"
    assert r["loe"] == "B"


def test_partner_age_warning():
    r = assess(_base(partnerAge=38))
    assert any("Partner age 38" in w for w in r["warnings"])
    # integer formatting, no trailing .0
    assert not any("38.0" in w for w in r["warnings"])


def test_no_partner_age_warning_at_37():
    # strictly > 37
    r = assess(_base(partnerAge=37))
    assert not any("Partner age" in w for w in r["warnings"])


def test_elevated_fsh_warning():
    r = assess(_base(fshLevel=12))
    assert any("Elevated FSH (12)" in w for w in r["warnings"])


def test_no_fsh_warning_at_threshold():
    r = assess(_base(fshLevel=10))
    assert not any("Elevated FSH" in w for w in r["warnings"])


def test_prior_varicocelectomy_warning():
    r = assess(_base(priorVaricocelectomy=True))
    assert any("Prior varicocelectomy" in w for w in r["warnings"])


def test_references_always_present():
    r = assess(_base())
    assert len(r["references"]) == 5
    assert any("Schlegel" in ref for ref in r["references"])


def test_warnings_stack_with_recommendation():
    r = assess(
        _base(
            grade="II",
            spermConcentration=10,
            infertilityDuration=12,
            partnerAge=40,
            fshLevel=15,
            priorVaricocelectomy=True,
        )
    )
    assert r["recommendation"] == "indicated"
    assert len(r["warnings"]) == 3
