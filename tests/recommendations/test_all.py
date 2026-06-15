"""Oracle tests for the ALL / CAR-T Pathway engine.

Ported 1:1 from old_static_code/server/hematology.test.ts
("ALL / CAR-T Pathway Tool" describe block).
"""

import re

from app.recommendations.modules.all import assess, get_cart_color, get_cart_label

BASE = {
    "age": 35,
    "ecogPS": 1,
    "fitnessStatus": "fit",
    "lineage": "b_all",
    "phase": "newly_diagnosed",
    "phStatus": "negative",
    "cnsStatus": "cns1",
    "hasT315IMutation": False,
    "hasKMT2ARearrangement": False,
    "hasIGH_CRLF2": False,
    "hasBCRABL1Like": False,
    "hasHyperdiploidy": False,
    "hasHypodiploidy": False,
    "hasTP53Mutation": False,
    "hasERG_deletion": False,
    "priorLines": 0,
    "priorBlinatumomab": False,
    "priorInotuzumab": False,
    "priorCARTCell": False,
    "mrdStatus": "unknown",
    "hasHLAMatchedDonor": True,
    "priorHCT": False,
    "patientPreference": "aggressive",
}


def _merge(**overrides):
    return {**BASE, **overrides}


def test_newly_diagnosed_ph_neg_b_all_fit_adult():
    # age 35 -> aya -> AYA protocol (CALGB/GRAALL)
    result = assess(_merge(age=45))  # adult to match "adult/induction" too; base age 35 is aya
    assert re.search(r"ECOG|CALGB|adult|induction|protocol", result["primaryLabel"], re.I)


def test_newly_diagnosed_ph_neg_base():
    result = assess(BASE)
    assert re.search(r"ECOG|CALGB|adult|induction|protocol", result["primaryLabel"], re.I)


def test_ph_positive_tki_based():
    result = assess(_merge(phStatus="positive"))
    assert re.search(r"TKI|dasatinib|ponatinib|ASCEND", result["primaryLabel"], re.I)


def test_ph_positive_t315i_warning():
    result = assess(_merge(phStatus="positive", hasT315IMutation=True))
    assert any(re.search(r"T315I|ponatinib", w, re.I) for w in result["keyWarnings"])


def test_rr_b_all_adult_no_prior_cart():
    result = assess(_merge(phase="relapsed_refractory", priorLines=1))
    assert re.search(
        r"CAR-T|KTE-X19|brexu|Brexu|blinatumomab|tisagenl|Kymriah|ZUMA",
        result["primaryLabel"],
        re.I,
    )


def test_cart_eligible_two_prior_lines():
    result = assess(_merge(phase="relapsed_refractory", priorLines=2, priorCARTCell=False))
    assert re.search(r"eligible", result["cartEligibility"], re.I)


def test_cart_already_received():
    result = assess(_merge(phase="relapsed_refractory", priorLines=3, priorCARTCell=True))
    assert result["cartEligibility"] == "already_received"


def test_t_all_nelarabine():
    result = assess(_merge(lineage="t_all"))
    assert re.search(r"nelarabine|Hyper-CVAD|T-ALL|T.ALL", result["primaryLabel"], re.I)


def test_mrd_positive_after_induction():
    result = assess(_merge(phase="mrd_positive", mrdStatus="positive_high"))
    assert any(
        re.search(r"escalat|blinatumomab|CAR-T|transplant", a, re.I)
        for a in result["mrdGuidedActions"]
    )


def test_elderly_unfit_low_intensity():
    result = assess(_merge(age=72, fitnessStatus="frail", ecogPS=3))
    assert re.search(
        r"low.intensity|mini|blinatumomab|BSC|supportive|frail",
        result["primaryLabel"],
        re.I,
    )


def test_pediatric_b_all():
    result = assess(_merge(age=8, fitnessStatus="fit"))
    assert re.search(r"COG|BFM|pediatric|Pediatric", result["primaryLabel"], re.I)


def test_cart_label_eligible_recommended():
    assert re.search(r"Recommended", get_cart_label("eligible_recommended"), re.I)


def test_cart_color_not_eligible():
    assert re.search(r"slate|gray|grey", get_cart_color("not_eligible"), re.I)


# ─── Additional branch / edge coverage (derived from TS branches) ──────────────
def test_bsc_preference():
    result = assess(_merge(patientPreference="bsc"))
    assert result["primaryRecommendation"] == "bsc_only"
    assert result["urgencyFlag"] == "routine"


def test_ecog_4_forces_bsc():
    result = assess(_merge(ecogPS=4))
    assert result["primaryRecommendation"] == "bsc_only"


def test_ph_positive_unfit_older_uses_tki_not_ascend():
    result = assess(_merge(phStatus="positive", age=65, fitnessStatus="unfit"))
    assert result["primaryRecommendation"] == "ph_positive_tki"


def test_ph_positive_fit_under60_uses_ascend():
    result = assess(_merge(phStatus="positive", age=45, fitnessStatus="fit"))
    assert result["primaryRecommendation"] == "dasatinib_blinatumomab"


def test_rr_ph_positive_t315i_ponatinib():
    result = assess(_merge(phase="relapsed_refractory", phStatus="positive", hasT315IMutation=True))
    assert result["primaryRecommendation"] == "ponatinib_blinatumomab"


def test_rr_pediatric_b_all_tisa():
    result = assess(_merge(phase="relapsed_refractory", age=10))
    assert result["primaryRecommendation"] == "cart_tisa"
    assert result["cartEligibility"] == "eligible_recommended"


def test_rr_t_all_clinical_trial():
    result = assess(_merge(phase="relapsed_refractory", lineage="t_all"))
    assert result["primaryRecommendation"] == "clinical_trial"
    assert result["cartEligibility"] == "not_eligible"


def test_cns3_warning_present():
    result = assess(_merge(cnsStatus="cns3"))
    assert any("CNS3" in w for w in result["keyWarnings"])


def test_fallback():
    # newly_diagnosed T-ALL but not fit -> falls through all newly-diagnosed
    # branches and there is no mrd/rr phase -> fallback
    result = assess(_merge(lineage="t_all", fitnessStatus="unfit"))
    # unfit + t_all newly diagnosed: not caught by older-adult-B-ALL (lineage
    # must be b_all), not by T-ALL-fit branch -> fallback
    assert result["primaryRecommendation"] == "clinical_trial"
    assert result["primaryLabel"] == "Clinical Trial / Specialist Consultation"
