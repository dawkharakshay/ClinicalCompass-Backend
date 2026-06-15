"""Tests for the Ovulation Induction Clinical Compass port.

Fixtures derived directly from the TS ``evaluate`` branches in
old_static_code/client/src/pages/OvulationInductionCompass.tsx (no .test.ts
oracle exists for this module).
"""

from app.recommendations.modules.ovulationinduction import assess


def _base(**over):
    d = {
        "anovulationCause": "pcos",
        "femaleAge": 0,
        "bmi": 0,
        "priorLetrozoleTrials": 0,
        "priorClomipheneTrials": 0,
        "priorMetforminTrials": 0,
        "priorGonadotropinTrials": 0,
        "tubalPatency": True,
        "normalSemenAnalysis": True,
        "hyperprolactinemiaTreated": False,
        "thyroidTreated": False,
    }
    d.update(over)
    return d


def test_hyperprolactinemia_untreated_not_indicated():
    r = assess(_base(anovulationCause="hyperprolactinemia", hyperprolactinemiaTreated=False))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Treat hyperprolactinemia first (dopamine agonist)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert r["rationale"][0].startswith("Hyperprolactinemia:")
    assert r["warnings"] == []


def test_thyroid_untreated_not_indicated():
    r = assess(_base(anovulationCause="thyroid", thyroidTreated=False))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Treat thyroid disorder first"
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_poi_contraindicated():
    r = assess(_base(anovulationCause="poi"))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Ovulation induction not effective for POI — consider donor oocyte"
    assert r["cor"] == "III"
    assert r["loe"] == "A"
    assert r["warnings"][0].startswith("Premature ovarian insufficiency")
    assert r["rationale"] == []


def test_pcos_first_line_letrozole():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=0, priorClomipheneTrials=0))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Letrozole (first-line for PCOS) — 2.5–7.5 mg days 3–7"
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_pcos_continue_letrozole():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=3))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Continue letrozole trials (3 completed, up to 6 recommended)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_pcos_first_line_when_clomiphene_used_but_no_letrozole():
    # priorLetrozole == 0 but priorClomiphene != 0 -> skips first-line, falls
    # to priorLetrozole < 6 branch (continue letrozole, 0 completed).
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=0, priorClomipheneTrials=2))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Continue letrozole trials (0 completed, up to 6 recommended)"


def test_pcos_gonadotropin_step_up():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=6, priorGonadotropinTrials=0))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Gonadotropin ovulation induction (FSH/LH) — step-up protocol"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("OHSS" in w for w in r["warnings"])


def test_pcos_consider_ivf_multiple_failures():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=6, priorGonadotropinTrials=3))
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "Consider IVF — multiple OI failures"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"


def test_pcos_high_bmi_warning():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=0, bmi=32))
    assert any(w.startswith("BMI 32:") for w in r["warnings"])


def test_pcos_bmi_below_30_no_warning():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=0, bmi=29.9))
    assert not any(w.startswith("BMI") for w in r["warnings"])


def test_bmi_decimal_formatting():
    r = assess(_base(anovulationCause="pcos", priorLetrozoleTrials=0, bmi=30.5))
    assert any(w.startswith("BMI 30.5:") for w in r["warnings"])


def test_unexplained_individualized():
    r = assess(_base(anovulationCause="unexplained"))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Ovulation induction — individualized protocol"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"


def test_hypothalamic_individualized():
    r = assess(_base(anovulationCause="hypothalamic"))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Ovulation induction — individualized protocol"
    assert r["cor"] == "IIa"


def test_hyperprolactinemia_treated_falls_through_to_individualized():
    # Treated hyperprolactinemia is not pcos/poi/thyroid -> else branch.
    r = assess(_base(anovulationCause="hyperprolactinemia", hyperprolactinemiaTreated=True))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Ovulation induction — individualized protocol"


def test_references_always_present():
    r = assess(_base())
    assert len(r["references"]) == 4
