"""Tests for the IVF Clinical Compass port.

No legacy oracle test exists in old_static_code/server. These fixtures are
derived directly from the branches of the inline ``evaluate()`` function in
old_static_code/client/src/pages/IVFCompass.tsx, covering each major decision
path (oncology, tubal, severe male factor, has-indication, IUI-consider,
not-indicated) plus the age/reserve/failed-cycle warnings.
"""

from __future__ import annotations

from app.recommendations.modules.ivf import assess


def _base() -> dict:
    """Default IVF inputs (mirrors defaultInputs)."""
    return {
        "femaleAge": 0,
        "infertilityDuration": "gt12",
        "ovarianReserve": "normal",
        "amhLevel": 0,
        "afcCount": 0,
        "maleFactor": "none",
        "tubalFactor": False,
        "uterineFactor": False,
        "endometriosis": False,
        "unexplained": False,
        "priorIUIAttempts": 0,
        "priorIVFAttempts": 0,
        "priorIVFSuccess": False,
        "stateMandate": False,
        "oncologyIndication": False,
    }


def test_oncology_takes_precedence():
    d = _base()
    d["oncologyIndication"] = True
    d["tubalFactor"] = True  # ensure oncology wins
    r = assess(d)
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "IVF with embryo cryopreservation (oncofertility)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("Time-sensitive" in w for w in r["warnings"])


def test_tubal_factor_first_line():
    d = _base()
    d["tubalFactor"] = True
    r = assess(d)
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "IVF (tubal factor infertility — first-line)"
    assert r["cor"] == "I"


def test_severe_male_factor_icsi():
    d = _base()
    d["maleFactor"] = "severe"
    r = assess(d)
    assert r["procedure"] == "IVF with ICSI (severe male factor)"
    assert r["recommendation"] == "indicated"


def test_azoospermia_icsi():
    d = _base()
    d["maleFactor"] = "azoospermia"
    r = assess(d)
    assert r["procedure"] == "IVF with ICSI (severe male factor)"


def test_has_indication_endometriosis():
    d = _base()
    d["endometriosis"] = True
    r = assess(d)
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "IVF"
    assert r["rationale"][0] == "Multiple infertility factors identified meeting ASRM criteria for IVF."


def test_has_indication_diminished_reserve():
    d = _base()
    d["ovarianReserve"] = "diminished"
    r = assess(d)
    assert r["procedure"] == "IVF"


def test_has_indication_iui_and_duration():
    d = _base()
    d["priorIUIAttempts"] = 3
    d["infertilityDuration"] = "gt12"
    r = assess(d)
    assert r["procedure"] == "IVF"


def test_consider_iui_trials():
    d = _base()
    d["infertilityDuration"] = "gt12"
    d["priorIUIAttempts"] = 1
    r = assess(d)
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "IUI trials before IVF (3 cycles recommended)"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"


def test_not_indicated():
    d = _base()
    d["infertilityDuration"] = "6to12"
    r = assess(d)
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Continue evaluation / IUI trials"


def test_success_rate_bands():
    bands = [
        (30, "~40–50% live birth per cycle"),
        (36, "~30–40% live birth per cycle"),
        (39, "~20–30% live birth per cycle"),
        (42, "~10–15% live birth per cycle"),
        (44, "~3–5% live birth per cycle (donor egg discussion recommended)"),
    ]
    for age, expected in bands:
        d = _base()
        d["femaleAge"] = age
        assert assess(d)["successRate"] == expected


def test_age_warning_and_interpolation():
    d = _base()
    d["femaleAge"] = 39
    r = assess(d)
    assert any(w.startswith("Age 39:") for w in r["warnings"])


def test_advanced_age_poor_reserve_warning():
    d = _base()
    d["femaleAge"] = 41
    d["ovarianReserve"] = "poor"
    r = assess(d)
    assert any("Advanced age + poor ovarian reserve" in w for w in r["warnings"])


def test_failed_ivf_cycles_warning():
    d = _base()
    d["priorIVFAttempts"] = 3
    d["priorIVFSuccess"] = False
    r = assess(d)
    assert any("3+ failed IVF cycles" in w for w in r["warnings"])


def test_failed_ivf_warning_suppressed_on_success():
    d = _base()
    d["priorIVFAttempts"] = 4
    d["priorIVFSuccess"] = True
    r = assess(d)
    assert not any("3+ failed IVF cycles" in w for w in r["warnings"])


def test_state_mandate_rationale():
    d = _base()
    d["stateMandate"] = True
    r = assess(d)
    assert any("State infertility mandate applies" in x for x in r["rationale"])


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 5
