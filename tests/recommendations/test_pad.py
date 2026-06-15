"""PAD Revascularization — ported 1:1 from old_static_code/server/pad.test.ts."""

import re

from app.recommendations.modules.pad import (
    assess,
    assess_risk_amplifiers,
    calculate_wifi_stage,
    get_cor_color,
    get_cor_label,
    get_modality_label,
    get_urgency_color,
    get_urgency_label,
)


# ─── Asymptomatic PAD ─────────────────────────────────────────────────────────

def test_asymptomatic_no_revasc():
    result = assess({"subset": "asymptomatic", "otherProcedureNeeded": False})
    assert result["revascularizationIndicated"] is False
    assert result["primaryRecommendation"]["cor"] == "3_harm"
    assert result["urgency"] in ("elective", "not_indicated")


def test_asymptomatic_facilitate_other_procedure():
    result = assess({"subset": "asymptomatic", "otherProcedureNeeded": True})
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] in ("2a", "2b", "1")
    assert result["urgency"] == "elective"


def test_asymptomatic_requires_gdmt():
    result = assess({"subset": "asymptomatic"})
    assert result["gdmtRequired"] is True


# ─── Claudication — GDMT not yet tried ────────────────────────────────────────

def test_claudication_gdmt_not_tried():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "not_tried",
        "functionallyLimiting": True,
        "anatomicLevel": "femoropopliteal",
    })
    assert result["revascularizationIndicated"] is False
    assert result["gdmtRequired"] is True
    assert result["exerciseTherapyRequired"] is True
    assert any(
        "gdmt" in m.lower() or "exercise" in m.lower() for m in result["keyMessages"]
    )


def test_claudication_gdmt_adequate():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "adequate",
        "functionallyLimiting": False,
    })
    assert result["revascularizationIndicated"] is False
    assert result["gdmtRequired"] is True


# ─── Claudication — Aortoiliac disease ────────────────────────────────────────

def test_claudication_aortoiliac():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "inadequate",
        "functionallyLimiting": True,
        "anatomicLevel": "aortoiliac",
        "hemodynamicallySignificant": True,
    })
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] in ("1", "2a")
    has_endo_cor1 = any(
        r["cor"] == "1" and r["loe"] == "A" for r in result["additionalRecommendations"]
    )
    assert has_endo_cor1 is True
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )


def test_claudication_aortoiliac_acceptable_risk():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "inadequate",
        "functionallyLimiting": True,
        "anatomicLevel": "aortoiliac",
        "hemodynamicallySignificant": True,
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )


# ─── Claudication — Femoropopliteal disease ───────────────────────────────────

def test_claudication_femoropopliteal():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "inadequate",
        "functionallyLimiting": True,
        "anatomicLevel": "femoropopliteal",
        "hemodynamicallySignificant": True,
    })
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] in ("2a", "1")
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )


def test_claudication_infrapopliteal_not_indicated():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "inadequate",
        "functionallyLimiting": True,
        "anatomicLevel": "infrapopliteal",
    })
    assert result["revascularizationIndicated"] is False
    has_uncertain = any(
        r["cor"] == "2b" or "infrapopliteal" in r["text"].lower()
        for r in result["additionalRecommendations"]
    )
    assert has_uncertain is True


# ─── Claudication — Common femoral artery ─────────────────────────────────────

def test_claudication_cfa_endarterectomy():
    result = assess({
        "subset": "claudication",
        "gdmtResponse": "inadequate",
        "functionallyLimiting": True,
        "anatomicLevel": "common_femoral",
        "hemodynamicallySignificant": True,
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] == "endarterectomy"
    has_cfa = any(
        re.search(r"common femoral|endarterectomy", r["text"].lower())
        for r in result["additionalRecommendations"]
    )
    assert has_cfa


# ─── CLTI — General ───────────────────────────────────────────────────────────

def test_clti_revasc_feasible():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "rest_pain",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] == "1"
    assert result["urgency"] == "urgent"
    assert result["multispecialtyTeamRequired"] is True


def test_clti_requires_multispecialty_team():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
    })
    assert result["multispecialtyTeamRequired"] is True


def test_clti_no_option():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "major_tissue_loss",
        "revascularizationFeasible": False,
    })
    assert result["revascularizationIndicated"] is False
    assert any(
        "no-option" in m.lower() or "amputation" in m.lower() or "palliative" in m.lower()
        for m in result["keyMessages"]
    )


# ─── CLTI — Conduit selection ─────────────────────────────────────────────────

def test_clti_adequate_gsv_acceptable_risk():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] in (
        "surgical_bypass", "surgical_preferred", "endovascular_or_surgical"
    )
    assert result["conduitNote"]


def test_clti_inadequate_gsv():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "conduitAvailability": "inadequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )


def test_clti_high_surgical_risk():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "rest_pain",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "high",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )


def test_clti_conduit_note_when_gsv_adequate():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["conduitNote"]
    assert re.search(r"gsv|saphenous|vein", result["conduitNote"].lower())


# ─── CLTI — CFA involvement ───────────────────────────────────────────────────

def test_clti_cfa_involvement():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "cfaInvolvement": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    all_text = " ".join(
        [result["primaryRecommendation"]["text"]]
        + [r["text"] for r in result["additionalRecommendations"]]
        + result["keyMessages"]
    ).lower()
    assert re.search(r"cfa|common femoral|endarterectomy", all_text)


# ─── Acute Limb Ischemia ──────────────────────────────────────────────────────

def test_ali_emergent():
    result = assess({"subset": "ali", "aliCategory": "IIb"})
    assert result["urgency"] == "emergent"


def test_ali_iia():
    result = assess({"subset": "ali", "aliCategory": "IIa"})
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] == "1"
    assert result["urgency"] in ("urgent", "emergent")


def test_ali_iib():
    result = assess({"subset": "ali", "aliCategory": "IIb"})
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] == "1"
    assert result["urgency"] == "emergent"


def test_ali_iii():
    result = assess({"subset": "ali", "aliCategory": "III"})
    assert result["revascularizationIndicated"] is False
    assert result["preferredModality"] in ("emergency_amputation", "amputation")
    assert result["urgency"] == "emergent"


def test_ali_category_i():
    result = assess({"subset": "ali", "aliCategory": "I"})
    assert result["urgency"] in ("urgent", "emergent")
    all_text = " ".join(
        [result["primaryRecommendation"]["text"]] + result["keyMessages"]
    ).lower()
    assert re.search(r"anticoagulation|heparin|monitor|imaging", all_text)


# ─── WIfI Classification ──────────────────────────────────────────────────────

def test_wifi_stage_low():
    result = calculate_wifi_stage(1, 1, 0)
    assert 1 <= result["stage"] <= 4


def test_wifi_stage_high():
    result = calculate_wifi_stage(3, 3, 3)
    assert result["stage"] == 4


def test_wifi_note_present():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "wifiWound": 2,
        "wifiIschemia": 2,
        "wifiFootInfection": 1,
    })
    assert result["wifiNote"]
    assert re.search(r"wifi|stage|wound|ischemia", result["wifiNote"].lower())


def test_wifi_note_absent():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "rest_pain",
        "revascularizationFeasible": True,
    })
    assert result.get("wifiNote") is None or result["wifiNote"] == ""


# ─── Risk Amplifiers ──────────────────────────────────────────────────────────

def test_amplifier_diabetes():
    amplifiers = assess_risk_amplifiers({"subset": "clti", "diabetes": True})
    assert any("diabetes" in a.lower() for a in amplifiers)


def test_amplifier_eskd():
    amplifiers = assess_risk_amplifiers({"subset": "clti", "eskd": True})
    assert any(re.search(r"eskd|kidney|renal", a.lower()) for a in amplifiers)


def test_amplifier_frailty():
    amplifiers = assess_risk_amplifiers({"subset": "clti", "frailty": True})
    assert any("frail" in a.lower() for a in amplifiers)


def test_amplifier_smoking():
    amplifiers = assess_risk_amplifiers({"subset": "claudication", "activeSmoker": True})
    assert any(re.search(r"smok|tobacco", a.lower()) for a in amplifiers)


def test_amplifier_none():
    amplifiers = assess_risk_amplifiers({
        "subset": "claudication",
        "diabetes": False,
        "ckd": False,
        "eskd": False,
        "frailty": False,
        "heartFailure": False,
        "severeLungDisease": False,
        "obesity": False,
        "activeSmoker": False,
        "polyvascularDisease": False,
    })
    assert len(amplifiers) == 0


def test_amplifiers_in_result():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "diabetes": True,
        "eskd": True,
    })
    assert len(result["riskAmplifiers"]) > 0


# ─── Utility Functions ────────────────────────────────────────────────────────

def test_get_cor_label():
    assert re.search(r"class i|cor 1|benefit", get_cor_label("1"), re.I)
    assert re.search(r"class iia|2a|moderate", get_cor_label("2a"), re.I)
    assert re.search(r"class iib|2b|weak", get_cor_label("2b"), re.I)
    assert re.search(r"class iii|harm|3", get_cor_label("3_harm"), re.I)
    assert re.search(r"class iii|no benefit|3", get_cor_label("3_no_benefit"), re.I)


def test_get_cor_color():
    assert get_cor_color("1")
    assert get_cor_color("2a")
    assert get_cor_color("3_harm")


def test_get_urgency_label():
    assert re.search(r"emergent", get_urgency_label("emergent"), re.I)
    assert re.search(r"urgent", get_urgency_label("urgent"), re.I)
    assert re.search(r"elective", get_urgency_label("elective"), re.I)


def test_get_urgency_color():
    assert get_urgency_color("emergent")
    assert get_urgency_color("urgent")
    assert get_urgency_color("elective")


def test_get_modality_label():
    assert re.search(r"endovascular", get_modality_label("endovascular"), re.I)
    assert re.search(r"bypass|surgical", get_modality_label("surgical_bypass"), re.I)
    assert re.search(r"endarterectomy", get_modality_label("endarterectomy"), re.I)
    assert re.search(r"hybrid", get_modality_label("hybrid"), re.I)
    assert re.search(r"amputation", get_modality_label("amputation"), re.I)
    assert re.search(
        r"none|not indicated|not recommended|uncertain", get_modality_label("none"), re.I
    )


# ─── Clinical Scenario Integration Tests ─────────────────────────────────────

def test_scenario_a():
    result = assess({
        "subset": "clti",
        "age": 65,
        "diabetes": True,
        "cltiPresentation": "minor_tissue_loss",
        "revascularizationFeasible": True,
        "conduitAvailability": "adequate_gsv",
        "surgicalRisk": "acceptable",
    })
    assert result["revascularizationIndicated"] is True
    assert result["urgency"] == "urgent"
    assert result["multispecialtyTeamRequired"] is True
    assert result["preferredModality"] in (
        "surgical_bypass", "surgical_preferred", "endovascular_or_surgical"
    )


def test_scenario_b():
    result = assess({
        "subset": "clti",
        "age": 78,
        "frailty": True,
        "cltiPresentation": "rest_pain",
        "revascularizationFeasible": True,
        "conduitAvailability": "inadequate_gsv",
        "surgicalRisk": "high",
    })
    assert result["revascularizationIndicated"] is True
    assert result["preferredModality"] in (
        "endovascular", "endovascular_preferred", "endovascular_or_surgical"
    )
    assert any("frail" in a.lower() for a in result["riskAmplifiers"])


def test_scenario_c():
    result = assess({
        "subset": "claudication",
        "age": 55,
        "activeSmoker": True,
        "gdmtResponse": "not_tried",
        "functionallyLimiting": True,
        "anatomicLevel": "femoropopliteal",
    })
    assert result["revascularizationIndicated"] is False
    assert result["gdmtRequired"] is True
    assert result["exerciseTherapyRequired"] is True


def test_scenario_d():
    result = assess({"subset": "ali", "aliCategory": "IIb", "age": 70})
    assert result["urgency"] == "emergent"
    assert result["revascularizationIndicated"] is True
    assert result["primaryRecommendation"]["cor"] == "1"


def test_scenario_e():
    result = assess({
        "subset": "asymptomatic",
        "otherProcedureNeeded": False,
        "age": 60,
        "diabetes": True,
    })
    assert result["revascularizationIndicated"] is False
    assert result["gdmtRequired"] is True


def test_scenario_f():
    result = assess({
        "subset": "clti",
        "cltiPresentation": "major_tissue_loss",
        "revascularizationFeasible": False,
        "diabetes": True,
        "eskd": True,
    })
    assert result["revascularizationIndicated"] is False
    assert len(result["riskAmplifiers"]) > 0
