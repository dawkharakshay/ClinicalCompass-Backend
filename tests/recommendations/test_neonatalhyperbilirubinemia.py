"""Oracle tests ported 1:1 from old_static_code/server/pediatrics.test.ts
(describe "Neonatal Hyperbilirubinemia Logic")."""

import re

from app.recommendations.modules.neonatalhyperbilirubinemia import assess

BASE_INPUT = {
    "gestationalAgeWeeks": 39,
    "gestationalAgeCategory": "term",
    "ageHours": 48,
    "totalSerumBilirubin": 10,
    "directBilirubin": 0.3,
    "hasIsoimmunization": False,
    "hasG6PDDeficiency": False,
    "hasAlbuminLow": False,
    "hasSepsis": False,
    "hasAcidosis": False,
    "hasAsphyxia": False,
    "isBreastfeedingOnly": True,
    "hasWeightLoss": False,
    "isEastAsianDescent": False,
    "hasAcuteBiliaryEncephalopathy": False,
    "hasKernicterus": False,
    "predischargeBilirubinZone": None,
    "currentlyOnPhototherapy": False,
    "hoursOnPhototherapy": 0,
    "bilirubinTrendRising": False,
}


def test_observe_decision_for_low_bilirubin_term_neonate():
    result = assess(BASE_INPUT)
    assert result["treatmentDecision"] == "observe"
    assert result["phototherapyThreshold"] > 10
    assert len(result["references"]) > 0


def test_recommends_phototherapy_when_tsb_exceeds_threshold():
    result = assess({**BASE_INPUT, "totalSerumBilirubin": 18})
    assert result["treatmentDecision"] in (
        "phototherapy",
        "intensive_phototherapy",
        "exchange_transfusion",
    )


def test_flags_acute_bilirubin_encephalopathy_for_emergency_exchange():
    result = assess(
        {
            **BASE_INPUT,
            "totalSerumBilirubin": 30,
            "hasAcuteBiliaryEncephalopathy": True,
        }
    )
    assert re.search(
        r"encephalopathy|KERNICTERUS|exchange",
        " ".join(result["urgentFlags"]),
        re.IGNORECASE,
    )


def test_flags_conjugated_hyperbilirubinemia_for_hepatology_referral():
    result = assess({**BASE_INPUT, "directBilirubin": 2.5})
    assert re.search(
        r"CONJUGATED|biliary atresia|hepatology",
        " ".join(result["urgentFlags"]),
        re.IGNORECASE,
    )


def test_lowers_phototherapy_threshold_for_isoimmunization():
    with_iso = assess({**BASE_INPUT, "hasIsoimmunization": True})
    without = assess(BASE_INPUT)
    assert with_iso["phototherapyThreshold"] <= without["phototherapyThreshold"]


def test_recommends_exchange_transfusion_when_tsb_exceeds_exchange_threshold():
    result = assess({**BASE_INPUT, "totalSerumBilirubin": 28, "ageHours": 72})
    assert result["treatmentDecision"] in (
        "exchange_transfusion",
        "intensive_phototherapy",
    )
