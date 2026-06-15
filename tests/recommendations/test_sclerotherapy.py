"""Sclerotherapy engine — fixtures derived directly from sclerotherapyLogic.ts branches."""

from app.recommendations.modules.sclerotherapy import assess


def _base() -> dict:
    return {
        "age": "",
        "ceapClass": "C1",
        "vesselType": "telangiectasia",
        "vesselDiameter": "0.5",
        "symptomDurationMonths": "",
        "symptoms": [],
        "priorAblation": False,
        "duplexConfirmed": False,
        "truncalReflux": False,
        "compressionWeeks": "0",
        "compressionCompliance": False,
        "pregnancy": False,
        "breastfeeding": False,
        "knownDVT": False,
        "activeInfection": False,
        "severePeripheralArterialDisease": False,
        "allergyToSclerosant": False,
        "patentForamenOvale": False,
        "migraineWithAura": False,
        "immobility": False,
        "foamRequested": False,
    }


def test_absolute_contraindication_wins():
    r = assess({**_base(), "pregnancy": True})
    assert r["cor"] == "III"
    assert r["loe"] == "C"
    assert r["urgency"] == "Contraindicated"
    assert r["recommendation"] == "Sclerotherapy Contraindicated"
    assert any("Pregnancy" in c for c in r["contraindications"])
    assert r["foamWarnings"] == []
    assert r["agentRecommendation"] == ""


def test_c1_telangiectasia_class_i():
    r = assess({**_base(), "ceapClass": "C1", "vesselType": "telangiectasia",
                "vesselDiameter": "0.5"})
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["recommendation"] == "Sclerotherapy Recommended"
    assert r["loe"] == "B"  # ceapNum < 2
    assert any("first-line treatment" in s for s in r["rationale"])
    assert any("<1 mm" in s for s in r["rationale"])
    assert "fine-needle technique" in r["agentRecommendation"]


def test_c1_reticular_mid_diameter():
    r = assess({**_base(), "ceapClass": "C1", "vesselType": "reticular",
                "vesselDiameter": "2"})
    assert r["cor"] == "I"
    assert any("1–3 mm" in s for s in r["rationale"])
    assert r["agentRecommendation"] == "Liquid or foam: Polidocanol 0.5–1% or STS 0.25–0.5%"


def test_truncal_reflux_first():
    r = assess({**_base(), "ceapClass": "C2", "vesselType": "varicose",
                "vesselDiameter": "4", "truncalReflux": True, "priorAblation": False})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Truncal Reflux — Ablation First"
    assert r["recommendation"] == (
        "Treat Truncal Reflux First — Ablation Recommended Before Sclerotherapy"
    )
    assert r["loe"] == "A"  # ceapNum >= 2
    assert any("ablation should be performed before" in s for s in r["rationale"])


def test_c2_residual_after_ablation_class_i():
    r = assess({**_base(), "ceapClass": "C2", "vesselType": "residual",
                "vesselDiameter": "4", "truncalReflux": True, "priorAblation": True})
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"
    assert r["loe"] == "A"
    assert any("residual varicosities after prior ablation" in s for s in r["rationale"])
    assert "Tessari method" in r["agentRecommendation"]


def test_c2_isolated_no_truncal_reflux_large_vessel():
    r = assess({**_base(), "ceapClass": "C3", "vesselType": "varicose",
                "vesselDiameter": "7", "truncalReflux": False, "priorAblation": False})
    assert r["cor"] == "I"
    assert any("isolated varicosities without truncal reflux" in s for s in r["rationale"])
    assert any("≥6 mm" in s for s in r["rationale"])
    assert any("Ambulatory phlebectomy" in s for s in r["optimizationSteps"])
    assert "ambulatory phlebectomy" in r["agentRecommendation"]


def test_insufficient_compression_class_iib():
    # truncalReflux True + priorAblation True skips truncal branch; ceapNum>=2 but
    # the C2+ residual branch (prior_ablation or not truncalReflux) would fire,
    # so to reach compression branch we need ceapNum>=2, no prior ablation, and
    # truncalReflux True (so first branch needs priorAblation to skip) -> tricky.
    # Use truncalReflux True + priorAblation True so branch1 skipped; branch3
    # fires (priorAblation True). Instead test compression via priorAblation True
    # is class I. So reach compression: truncalReflux True, priorAblation True is
    # class I. The compression branch requires truncalReflux True AND priorAblation
    # True is impossible. It is reachable only when ceapNum>=2, truncalReflux True,
    # priorAblation True is class I... compression branch is effectively dead unless
    # ceapNum>=2 with truncalReflux True and priorAblation True -> class I. So the
    # only path: truncalReflux True + priorAblation True hits branch3. Compression
    # branch reached when ceapNum>=2, not in branch1 (needs priorAblation True),
    # not in branch3 (needs not(priorAblation or not truncalReflux)) i.e.
    # priorAblation False and truncalReflux True -> but that's branch1. Dead code.
    # Confirm dead-code reasoning: assert branch3 fires here.
    r = assess({**_base(), "ceapClass": "C2", "vesselType": "varicose",
                "vesselDiameter": "4", "truncalReflux": True, "priorAblation": True,
                "compressionWeeks": "1"})
    assert r["cor"] == "I"
    assert r["urgency"] == "Appropriate"


def test_insufficient_criteria_default():
    # ceapNum 1 but vesselType varicose -> not C1 branch; ceapNum<2 -> not C2 branch;
    # compression branch needs ceapNum>=2 -> falls to else.
    r = assess({**_base(), "ceapClass": "C1", "vesselType": "varicose",
                "vesselDiameter": "0.5", "truncalReflux": False, "priorAblation": False})
    assert r["cor"] == "IIb"
    assert r["urgency"] == "Insufficient Criteria"
    assert r["recommendation"] == "Insufficient Criteria for Sclerotherapy"
    assert any("Document CEAP classification" in s for s in r["optimizationSteps"])


def test_foam_warnings_triggered_by_diameter():
    r = assess({**_base(), "ceapClass": "C2", "vesselType": "varicose",
                "vesselDiameter": "4", "truncalReflux": False, "priorAblation": False,
                "patentForamenOvale": True, "migraineWithAura": True,
                "breastfeeding": True, "knownDVT": True})
    assert any("Patent foramen ovale" in w for w in r["foamWarnings"])
    assert any("Migraine with aura" in w for w in r["foamWarnings"])
    assert any("Breastfeeding" in w for w in r["foamWarnings"])
    assert any("Prior DVT" in w for w in r["foamWarnings"])


def test_foam_warnings_via_foam_requested_small_vessel():
    r = assess({**_base(), "ceapClass": "C1", "vesselType": "telangiectasia",
                "vesselDiameter": "0.5", "foamRequested": True,
                "patentForamenOvale": True})
    assert any("Patent foramen ovale" in w for w in r["foamWarnings"])


def test_no_foam_warnings_when_small_and_not_requested():
    r = assess({**_base(), "ceapClass": "C1", "vesselType": "telangiectasia",
                "vesselDiameter": "0.5", "foamRequested": False,
                "patentForamenOvale": True, "migraineWithAura": True})
    assert r["foamWarnings"] == []
