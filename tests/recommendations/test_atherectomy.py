"""Tests for the Peripheral Atherectomy engine.

No legacy *.test.ts oracle exists for atherectomyLogic.ts, so these fixtures
are derived directly from the TS decision branches in
old_static_code/client/src/lib/atherectomyLogic.ts, covering each major path
plus the contraindication/asymptomatic edge.
"""

from __future__ import annotations

from app.recommendations.modules.atherectomy import assess


def _base(**overrides) -> dict:
    data = {
        "rutherfordCategory": "2",
        "tascClass": "A",
        "glassStage": "I",
        "lesionType": "de_novo",
        "calcificationGrade": "none",
        "lesionLengthCm": 5,
        "vesselDiameterMm": 5,
        "vesselTerritory": "femoropopliteal",
        "medicalTherapyOptimized": True,
        "smokingCessationCounseled": True,
        "diabetesMellitus": False,
        "renalInsufficiency": False,
        "priorBypass": False,
        "priorStent": False,
        "criticalLimbIschemiaPresent": False,
        "woundPresent": False,
        "ankleIndexABI": 0.9,
    }
    data.update(overrides)
    return data


def test_asymptomatic_not_indicated():
    r = assess(_base(rutherfordCategory="0"))
    assert r["recommendation"] == "not_indicated"
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["deviceRecommendation"] == "not_indicated"
    assert any("Class III" in x for x in r["rationale"])


def test_cli_via_rutherford_indicated_with_wound():
    r = assess(
        _base(
            rutherfordCategory="5",
            tascClass="C",
            glassStage="II",
            calcificationGrade="severe",
            woundPresent=True,
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    # CLI + femoropopliteal + calcified -> orbital device
    assert r["deviceRecommendation"] == "orbital"
    assert any("GLASS Stage II / TASC C" in x for x in r["rationale"])
    assert any("Wound present" in x for x in r["rationale"])


def test_cli_via_flag_infrapopliteal_laser():
    r = assess(
        _base(
            rutherfordCategory="3",
            criticalLimbIschemiaPresent=True,
            vesselTerritory="infrapopliteal",
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "I"
    assert r["deviceRecommendation"] == "laser"


def test_claudication_complex_lesion_reasonable():
    r = assess(_base(rutherfordCategory="3", tascClass="D", glassStage="I"))
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"
    assert any("complex anatomy" in x for x in r["rationale"])


def test_claudication_calcified_reasonable():
    r = assess(
        _base(
            rutherfordCategory="2",
            tascClass="A",
            glassStage="I",
            calcificationGrade="moderate",
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "IIa"
    # not ISR -> calcification rationale
    assert any("Moderate-to-severe calcification" in x for x in r["rationale"])
    # femoropopliteal + calcified -> orbital
    assert r["deviceRecommendation"] == "orbital"


def test_claudication_isr_reasonable():
    r = assess(
        _base(
            rutherfordCategory="2",
            tascClass="A",
            glassStage="I",
            lesionType="in_stent_restenosis",
        )
    )
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "IIa"
    assert any("In-stent restenosis" in x for x in r["rationale"])
    # femoropopliteal + ISR (not calcified) -> laser
    assert r["deviceRecommendation"] == "laser"


def test_claudication_simple_consider():
    r = assess(_base(rutherfordCategory="2", tascClass="A", glassStage="I"))
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"
    # femoropopliteal, de_novo, no calc -> directional device
    assert r["deviceRecommendation"] == "directional"


def test_rutherford_one_not_indicated_fallthrough():
    # Rutherford 1 = mild claudication: not CLI, not isClaudication, not asymptomatic
    r = assess(_base(rutherfordCategory="1"))
    assert r["recommendation"] == "not_indicated"
    assert r["cor"] == "III"
    assert r["loe"] == "C"


def test_warnings_emitted():
    r = assess(
        _base(
            medicalTherapyOptimized=False,
            smokingCessationCounseled=False,
            renalInsufficiency=True,
            criticalLimbIschemiaPresent=True,
            ankleIndexABI=0.3,
        )
    )
    assert any("Medical therapy" in x for x in r["warnings"])
    assert any("Smoking cessation" in x for x in r["warnings"])
    assert any("Renal insufficiency" in x for x in r["warnings"])
    assert any("ABI < 0.4 with CLI" in x for x in r["warnings"])


def test_abi_warning_requires_cli():
    # low ABI but no CLI -> no ABI warning
    r = assess(_base(rutherfordCategory="2", ankleIndexABI=0.3))
    assert not any("ABI < 0.4 with CLI" in x for x in r["warnings"])


def test_aortoiliac_rotational_device():
    r = assess(_base(rutherfordCategory="2", vesselTerritory="aortoiliac"))
    assert r["deviceRecommendation"] == "rotational"


def test_references_always_present():
    r = assess(_base())
    assert len(r["references"]) == 8
