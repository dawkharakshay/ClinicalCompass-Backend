"""Tests for the Peyronie's Disease Surgery port.

Oracle: old_static_code/client/src/pages/PeyroniesCompass.tsx evaluate().
Fixtures derived from each TS decision branch.
"""

from app.recommendations.modules.peyronies import assess


def _base(**over):
    d = {
        "diseasePhase": "chronic",
        "curvatureDegrees": 0,
        "curvatureDirection": "dorsal",
        "hinge": False,
        "hourglass": False,
        "penisShorteningCm": 0,
        "erDysfunction": "none",
        "iief5Score": 0,
        "pdeInhibitorResponse": True,
        "priorCollagenaseInjections": False,
        "priorSurgery": False,
        "stableMonths": 24,
        "sexuallyActive": True,
        "partnerConsent": True,
    }
    d.update(over)
    return d


def test_acute_phase_contraindicated():
    r = assess(_base(diseasePhase="acute"))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Non-surgical management — disease not yet stable"
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert any("Acute phase" in w for w in r["warnings"])


def test_unstable_less_than_12_months():
    r = assess(_base(stableMonths=8, curvatureDegrees=45))
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Continue observation — await 12 months of stability"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert any("stable for only 8 months" in w for w in r["warnings"])


def test_curvature_below_30_observation():
    r = assess(_base(curvatureDegrees=20))
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "Observation or non-surgical management"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"


def test_severe_ed_gets_ipp():
    r = assess(_base(curvatureDegrees=45, erDysfunction="severe", iief5Score=20))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Penile Prosthesis Implantation (IPP) with intraoperative modeling"
    assert r["cor"] == "I"


def test_low_iief5_gets_ipp():
    # erDysfunction not severe but IIEF-5 < 11 still routes to IPP
    r = assess(_base(curvatureDegrees=45, erDysfunction="mild", iief5Score=9))
    assert r["procedure"] == "Penile Prosthesis Implantation (IPP) with intraoperative modeling"


def test_plication_for_moderate_simple_curvature():
    r = assess(
        _base(
            curvatureDegrees=50,
            erDysfunction="none",
            iief5Score=22,
            hinge=False,
            hourglass=False,
            penisShorteningCm=0.5,
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Plication (Nesbit/modified Nesbit) — shortening procedure"
    assert r["cor"] == "I"
    assert r["loe"] == "B"


def test_grafting_for_severe_curvature():
    r = assess(_base(curvatureDegrees=70, erDysfunction="none", iief5Score=22))
    assert r["procedure"] == "Plaque Incision/Excision with Grafting (Lue procedure)"
    assert any("higher risk of post-operative ED" in w for w in r["warnings"])


def test_grafting_for_hourglass_even_if_low_curvature():
    r = assess(
        _base(curvatureDegrees=40, erDysfunction="none", iief5Score=22, hourglass=True)
    )
    assert r["procedure"] == "Plaque Incision/Excision with Grafting (Lue procedure)"
    assert any("Hourglass deformity" in w for w in r["warnings"])


def test_grafting_for_significant_shortening():
    r = assess(
        _base(curvatureDegrees=40, erDysfunction="none", iief5Score=22, penisShorteningCm=1.5)
    )
    assert r["procedure"] == "Plaque Incision/Excision with Grafting (Lue procedure)"


def test_hinge_warning_and_grafting():
    r = assess(_base(curvatureDegrees=40, erDysfunction="none", iief5Score=22, hinge=True))
    assert r["procedure"] == "Plaque Incision/Excision with Grafting (Lue procedure)"
    assert any("Hinge deformity present" in w for w in r["warnings"])


def test_partner_not_counseled_warning():
    r = assess(_base(curvatureDegrees=20, partnerConsent=False))
    assert any("Partner has not been counseled" in w for w in r["warnings"])


def test_no_partner_warning_when_consented():
    r = assess(_base(curvatureDegrees=20, partnerConsent=True))
    assert not any("Partner has not been counseled" in w for w in r["warnings"])


def test_prior_collagenase_rationale_when_curvature_above_30():
    r = assess(
        _base(
            curvatureDegrees=45,
            erDysfunction="none",
            iief5Score=22,
            priorCollagenaseInjections=True,
        )
    )
    assert any("Prior collagenase injections" in x for x in r["rationale"])


def test_prior_collagenase_no_rationale_when_curvature_30_or_below():
    r = assess(
        _base(
            curvatureDegrees=30,
            stableMonths=24,
            priorCollagenaseInjections=True,
        )
    )
    # curvature 30 -> not > 30, so no collagenase rationale
    assert not any("Prior collagenase injections" in x for x in r["rationale"])


def test_boundary_curvature_30_is_surgical_candidate():
    # 30 is not < 30, so falls into surgical-candidate branch
    r = assess(_base(curvatureDegrees=30, erDysfunction="none", iief5Score=22))
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Plication (Nesbit/modified Nesbit) — shortening procedure"


def test_boundary_curvature_60_is_plication():
    r = assess(_base(curvatureDegrees=60, erDysfunction="none", iief5Score=22))
    assert r["procedure"] == "Plication (Nesbit/modified Nesbit) — shortening procedure"


def test_iief5_11_is_not_low():
    # iief5 == 11 is NOT < 11, so not forced to IPP
    r = assess(_base(curvatureDegrees=45, erDysfunction="none", iief5Score=11))
    assert r["procedure"] == "Plication (Nesbit/modified Nesbit) — shortening procedure"


def test_result_keys():
    r = assess(_base(curvatureDegrees=45, iief5Score=22))
    assert set(r.keys()) == {
        "recommendation",
        "procedure",
        "cor",
        "loe",
        "warnings",
        "rationale",
        "references",
    }
