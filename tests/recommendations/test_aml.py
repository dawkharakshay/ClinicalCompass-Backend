"""Tests for the AML Clinical Compass engine.

Cases 1:1 ported from old_static_code/server/hematology.test.ts (AML Decision
Engine block), plus added decision-path fixtures derived from the TS branches.
"""

from __future__ import annotations

import re

import pytest

from app.recommendations.modules.aml import (
    assess,
    assess_fitness,
    classify_eln_risk,
)


# Base input: fit patient, intermediate risk, no mutations
BASE = {
    "age": 55,
    "ecogPS": 1,
    "creatinine": "normal",
    "bilirubin": "normal",
    "ejectionFraction": "normal_45plus",
    "hctCI": 0,
    "patientPreference": "aggressive",
    "isAPL": False,
    "isSecondaryAML": False,
    "isRelapsedRefractory": False,
    "karyotype": "normal",
    "npm1Mutation": False,
    "flt3ITD": False,
    "flt3ITDAllelicRatio": "na",
    "flt3TKD": False,
    "idh1Mutation": False,
    "idh2Mutation": False,
    "tp53Mutation": False,
    "runx1Mutation": False,
    "asxl1Mutation": False,
    "bcorMutation": False,
    "cebpaDoubleMutation": False,
    "hasHLAMatchedSibling": True,
    "hasMatchedUnrelatedDonor": False,
    "priorHCT": False,
}


def merge(**overrides) -> dict:
    return {**BASE, **overrides}


# ─── Ported 1:1 from hematology.test.ts ───────────────────────────────────────


def test_fit_intermediate_7_3():
    result = assess(BASE)
    assert re.search(r"7\+3|Induction|induction", result["primaryTherapyLabel"])
    assert result["transplantRecommendation"]


def test_unfit_age78_ecog3_ven_hma():
    result = assess(merge(age=78, ecogPS=3))
    assert re.search(r"venetoclax|VEN|Ven|HMA", result["primaryTherapyLabel"])


def test_flt3_itd_midostaurin_addition():
    result = assess(merge(flt3ITD=True, flt3ITDAllelicRatio="high"))
    assert any(re.search(r"midostaurin", a, re.I) for a in result["targetedAdditions"])


def test_idh1_ivosidenib_addition():
    result = assess(merge(idh1Mutation=True))
    assert any(re.search(r"ivosidenib", a, re.I) for a in result["targetedAdditions"])


def test_idh2_enasidenib_addition():
    result = assess(merge(idh2Mutation=True))
    assert any(re.search(r"enasidenib", a, re.I) for a in result["targetedAdditions"])


def test_cbf_t8_21_favorable():
    assert classify_eln_risk(merge(karyotype="favorable_t8_21")) == "favorable"


def test_tp53_adverse():
    assert classify_eln_risk(merge(tp53Mutation=True)) == "adverse"


def test_npm1_without_flt3_favorable():
    assert classify_eln_risk(merge(npm1Mutation=True, flt3ITD=False)) == "favorable"


def test_relapsed_refractory_warning_urgent():
    result = assess(merge(isRelapsedRefractory=True))
    assert any(
        re.search(r"salvage|Relapsed|gilteritinib|FLAG-IDA|clinical trial", w, re.I)
        for w in result["keyWarnings"]
    )
    assert result["urgencyFlag"] == "urgent"


def test_elderly_unfit_low_intensity():
    result = assess(merge(age=78, ecogPS=3, hctCI=3))
    assert re.search(
        r"venetoclax|HMA|azacitidine|decitabine", result["primaryTherapyLabel"], re.I
    )


def test_bsc_preference_palliative():
    result = assess(merge(patientPreference="bsc"))
    assert re.search(r"supportive|palliative|BSC", result["primaryTherapyLabel"], re.I)


def test_apl_atra_ato_emergent():
    result = assess(merge(isAPL=True))
    assert re.search(r"ATRA|ATO|arsenic", result["primaryTherapyLabel"])
    assert result["urgencyFlag"] == "emergent"


def test_fitness_ecog4_bsc_only():
    assert assess_fitness(merge(ecogPS=4)) == "bsc_only"


# ─── Added branch-coverage fixtures ───────────────────────────────────────────


def test_fit_intermediate_exact_therapy_and_transplant():
    result = assess(BASE)
    assert result["fitnessCategory"] == "fit"
    assert result["elnRisk"] == "intermediate"
    assert result["primaryTherapy"] == "ic_7_3"
    assert result["transplantRecommendation"] == "consider_cr1"
    assert result["urgencyFlag"] == "routine"


def test_fit_flt3_midostaurin_therapy():
    result = assess(merge(flt3ITD=True))
    assert result["primaryTherapy"] == "ic_7_3_midostaurin"


def test_fit_idh1_therapy():
    result = assess(merge(idh1Mutation=True))
    assert result["primaryTherapy"] == "ic_7_3_ivosidenib"


def test_fit_idh2_therapy():
    result = assess(merge(idh2Mutation=True))
    assert result["primaryTherapy"] == "ic_7_3_enasidenib"


def test_unfit_idh1_alt_therapy():
    result = assess(merge(age=78, idh1Mutation=True))
    assert result["fitnessCategory"] == "unfit"
    assert result["primaryTherapy"] == "alt_hma_ven_ivosidenib"


def test_unfit_idh2_alt_therapy():
    result = assess(merge(age=78, idh2Mutation=True))
    assert result["primaryTherapy"] == "alt_hma_ven_enasidenib"


def test_unfit_flt3_alt_therapy():
    result = assess(merge(age=78, flt3ITD=True))
    assert result["primaryTherapy"] == "alt_hma_ven_flt3i"


def test_unfit_standard_alt_therapy_and_transplant():
    result = assess(merge(age=78))
    assert result["primaryTherapy"] == "alt_hma_ven"
    assert result["transplantRecommendation"] == "after_alt_response"


def test_adverse_fit_with_donor_strongly_recommended():
    result = assess(merge(tp53Mutation=True, hasHLAMatchedSibling=True))
    assert result["elnRisk"] == "adverse"
    assert result["transplantRecommendation"] == "strongly_recommended_cr1"
    assert result["urgencyFlag"] == "urgent"


def test_adverse_fit_no_donor_recommended():
    result = assess(
        merge(tp53Mutation=True, hasHLAMatchedSibling=False, hasMatchedUnrelatedDonor=False)
    )
    assert result["transplantRecommendation"] == "recommended_cr1"


def test_favorable_fit_transplant_not_recommended():
    result = assess(merge(karyotype="favorable_inv16"))
    assert result["elnRisk"] == "favorable"
    assert result["transplantRecommendation"] == "not_recommended_cr1"


def test_apl_transplant_not_recommended_cr1():
    result = assess(merge(isAPL=True))
    assert result["transplantRecommendation"] == "not_recommended_cr1"


def test_prior_hct_not_candidate():
    result = assess(merge(priorHCT=True))
    assert result["transplantRecommendation"] == "not_candidate"
    assert "Prior HCT" in result["transplantRationale"]


def test_bsc_only_not_candidate():
    result = assess(merge(patientPreference="bsc"))
    assert result["fitnessCategory"] == "bsc_only"
    assert result["primaryTherapy"] == "bsc"
    assert result["transplantRecommendation"] == "not_candidate"


def test_runx1_without_npm1_adverse():
    assert classify_eln_risk(merge(runx1Mutation=True)) == "adverse"


def test_runx1_with_npm1_not_adverse_via_runx1():
    # npm1 present blocks the runx1 adverse path; npm1 without flt3 -> favorable
    assert classify_eln_risk(merge(runx1Mutation=True, npm1Mutation=True)) == "favorable"


def test_cebpa_double_favorable():
    assert classify_eln_risk(merge(cebpaDoubleMutation=True)) == "favorable"


def test_secondary_aml_addition():
    result = assess(merge(isSecondaryAML=True))
    assert any(re.search(r"CPX-351", a) for a in result["targetedAdditions"])


def test_age75_flt3_warning():
    result = assess(merge(age=78, flt3ITD=True))
    assert any(re.search(r"≥75 receiving HMA\+VEN", w) for w in result["keyWarnings"])


def test_two_moderate_factors_unfit():
    # age 65-74 (moderate) + ecog 2 (moderate) -> 2 moderate factors -> unfit
    result = assess(merge(age=68, ecogPS=2))
    assert result["fitnessCategory"] == "unfit"


def test_one_moderate_factor_fit():
    result = assess(merge(age=68, ecogPS=1))
    assert result["fitnessCategory"] == "fit"


def test_string_inputs_coerced():
    # Form fields arrive as strings for numbers; ensure coercion matches.
    result = assess(merge(age="78", ecogPS="3"))
    assert result["fitnessCategory"] == "unfit"


def test_references_present():
    result = assess(BASE)
    ids = [r["id"] for r in result["references"]]
    assert ids == ["ash2025", "eln2022", "eln2024", "viale_a", "ratify"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
