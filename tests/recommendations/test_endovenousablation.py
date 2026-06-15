"""Tests for the Endovenous Ablation port.

No oracle .test.ts exists for endovenousAblationLogic.ts; fixtures are derived
directly from the TS decision branches in assessEndovenousAblation.
"""

from __future__ import annotations

from app.recommendations.modules.endovenousablation import assess


def _base(**overrides) -> dict:
    data = {
        "age": "55",
        "ceapClass": "C2",
        "gsv": True,
        "ssv": False,
        "refluxDuration": "1.2",
        "veinDiameter": "6",
        "vcssScore": "5",
        "symptomDurationMonths": "12",
        "symptoms": [],
        "conservativeTherapyWeeks": "6",
        "compressionStockings": True,
        "compressionWeeks": "6",
        "duplexConfirmed": True,
        "standingReflux": True,
        "priorDVT": False,
        "activeUlcer": False,
        "nonAmbulatory": False,
        "pregnancy": False,
        "activeInfection": False,
        "coagulopathy": False,
        "preferredModality": "laser",
    }
    data.update(overrides)
    return data


def test_contraindication_pregnancy():
    r = assess(_base(pregnancy=True))
    assert r["cor"] == "III"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Endovenous Ablation Contraindicated"
    assert r["loe"] == "C"
    assert "Pregnancy — defer elective ablation until postpartum" in r["contraindications"]
    assert r["modalityNote"] == ""


def test_contraindications_multiple_collected_in_order():
    r = assess(
        _base(pregnancy=True, activeInfection=True, nonAmbulatory=True, coagulopathy=True)
    )
    assert r["contraindications"] == [
        "Pregnancy — defer elective ablation until postpartum",
        "Active skin/soft tissue infection overlying target vein — treat infection first",
        "Non-ambulatory patient — endovenous ablation not indicated; consider compression only",
        "Uncorrected coagulopathy — manage anticoagulation per procedural guidelines",
    ]


def test_class_i_appropriate_gsv():
    r = assess(_base())
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Endovenous Ablation Recommended"
    assert r["loe"] == "B"  # ceap 2 -> B
    assert (
        "CEAP C2 with duplex-confirmed GSV reflux ≥1.2s in standing position"
        in r["rationale"]
    )
    assert "Compression therapy trial completed (≥3 weeks)" in r["rationale"]


def test_class_i_urgent_ulcer_c6():
    r = assess(_base(ceapClass="C6"))
    assert r["cor"] == "I"
    assert r["urgency"] == "Urgent (Active/Healed Ulcer)"
    assert r["loe"] == "A"  # ceap >= 4
    assert any("ablation reduces ulcer recurrence by 50–70%" in x for x in r["rationale"])


def test_class_i_integer_reflux_no_trailing_zero():
    # refluxDuration "2" should render as "2" not "2.0" in the rationale
    r = assess(_base(refluxDuration="2"))
    assert r["cor"] == "I"
    assert (
        "CEAP C2 with duplex-confirmed GSV reflux ≥2s in standing position"
        in r["rationale"]
    )


def test_class_iia_no_standing_reflux():
    r = assess(_base(standingReflux=False))
    assert r["cor"] == "IIa"
    assert r["urgency"] == "Reasonable"
    assert r["recommendation"] == "Endovenous Ablation Reasonable"
    assert "CEAP C2 with duplex-confirmed truncal reflux" in r["rationale"]


def test_class_iia_borderline_reflux_optimization_note():
    r = assess(_base(standingReflux=False, refluxDuration="0.3"))
    assert r["cor"] == "IIa"
    assert any("Reflux duration <0.5s" in x for x in r["optimizationSteps"])


def test_class_iib_c1_disease():
    r = assess(_base(ceapClass="C1"))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Symptomatic C1 — Consider Conservative Management"
    assert r["recommendation"] == "Insufficient Criteria for Ablation"
    assert r["loe"] == "C"  # ceap 1 -> C
    assert "Consider sclerotherapy for isolated C1 disease" in r["optimizationSteps"]


def test_class_iib_insufficient_compression():
    r = assess(_base(compressionWeeks="1"))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Continue Compression Therapy"
    assert r["recommendation"] == "Continue Compression Therapy — Ablation Premature"
    assert any("graduated compression stockings" in x for x in r["optimizationSteps"])


def test_class_iib_duplex_required():
    # compressionWeeks>=3 but duplex not confirmed -> falls to duplex branch
    r = assess(_base(duplexConfirmed=False, ceapClass="C3"))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Duplex Ultrasound Required"
    assert r["recommendation"] == "Duplex Ultrasound Required Before Ablation"


def test_class_iib_insufficient_criteria():
    # ceap>=2, duplex confirmed, compression>=3, but no GSV/SSV reflux
    r = assess(_base(gsv=False, ssv=False))
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert r["recommendation"] == "Insufficient Criteria for Ablation"
    assert "Ensure CEAP C2 or higher is documented" in r["optimizationSteps"]


def test_modality_note_large_vein():
    r = assess(_base(veinDiameter="14"))
    assert "RFA may have higher occlusion rates" in r["modalityNote"]


def test_modality_note_small_vein():
    r = assess(_base(veinDiameter="2"))
    assert "technically challenging" in r["modalityNote"]


def test_modality_note_standard_vein():
    r = assess(_base(veinDiameter="6"))
    assert "standard range (3–12 mm)" in r["modalityNote"]


def test_prior_dvt_rationale_appended():
    r = assess(_base(priorDVT=True))
    assert any("Prior DVT" in x for x in r["rationale"])


def test_vcss_rationale_appended_integer_format():
    r = assess(_base(vcssScore="8"))
    assert "VCSS 8 (moderate-severe) — supports medical necessity for ablation" in r["rationale"]


def test_vcss_below_threshold_not_appended():
    r = assess(_base(vcssScore="7"))
    assert not any("VCSS" in x for x in r["rationale"])
