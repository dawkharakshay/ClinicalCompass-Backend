"""Tests for the psoriasis module, derived 1:1 from the TS branches in
old_static_code/client/src/lib/psoriasisLogic.ts (no TS test existed)."""

from app.recommendations.modules.psoriasis import assess


def _base(**overrides):
    data = {
        "bsaPercent": 0,
        "dlqi": 0,
        "pgaScore": 0,
        "subtype": "plaque",
        "specialSites": [],
        "hasPsoriaticArthritis": False,
        "hasNailInvolvement": False,
        "priorTreatment": "none",
        "hasCardiovascularDisease": False,
        "hasInflammatoryBowelDisease": False,
        "hasDemyelinatingDisease": False,
        "hasActiveTuberculosis": False,
        "hasChronicHBV": False,
        "hasHepaticImpairment": False,
        "hasMalignancyHistory": False,
        "isImmunocompromised": False,
        "isPregnant": False,
        "isBreastfeeding": False,
        "prefersOralTherapy": False,
        "hasObesity": False,
        "hasMetabolicSyndrome": False,
    }
    data.update(overrides)
    return data


# ---- Severity classification ----

def test_mild_severity():
    r = assess(_base(bsaPercent=2, dlqi=3, pgaScore=2))
    assert r["severity"] == "mild"
    assert r["primaryRecommendation"].startswith("Topical therapy")
    assert any("Taclonex" in a for a in r["firstLineAgents"])
    assert r["treatToTargetGoal"] == "Clear or near-clear (BSA <1%) within 3 months"


def test_moderate_by_bsa():
    r = assess(_base(bsaPercent=5, dlqi=3, pgaScore=2))
    assert r["severity"] == "moderate"
    assert r["primaryRecommendation"].startswith("Systemic therapy")


def test_moderate_by_dlqi():
    r = assess(_base(bsaPercent=2, dlqi=6, pgaScore=2))
    assert r["severity"] == "moderate"


def test_moderate_by_pga_three():
    r = assess(_base(bsaPercent=1, dlqi=1, pgaScore=3))
    assert r["severity"] == "moderate"


def test_moderate_by_special_site():
    r = assess(_base(specialSites=["palmoplantar"]))
    assert r["severity"] == "moderate"


def test_moderate_by_psa_special_site():
    r = assess(_base(hasPsoriaticArthritis=True))
    assert r["severity"] == "moderate"


def test_severe_by_bsa():
    r = assess(_base(bsaPercent=15, dlqi=2, pgaScore=2))
    assert r["severity"] == "severe"
    assert r["primaryRecommendation"].startswith("Biologic therapy")


def test_severe_by_dlqi():
    r = assess(_base(bsaPercent=2, dlqi=11, pgaScore=2))
    assert r["severity"] == "severe"


def test_severe_by_pga_four():
    r = assess(_base(bsaPercent=2, dlqi=2, pgaScore=4))
    assert r["severity"] == "severe"


def test_erythrodermic_is_severe_regardless():
    r = assess(_base(subtype="erythrodermic", bsaPercent=0, dlqi=0, pgaScore=0))
    assert r["severity"] == "severe"


def test_pustular_generalized_is_severe_regardless():
    r = assess(_base(subtype="pustular_generalized", bsaPercent=0, dlqi=0, pgaScore=0))
    assert r["severity"] == "severe"


# ---- Urgent flags ----

def test_erythrodermic_urgent_flag():
    r = assess(_base(subtype="erythrodermic"))
    assert any("Erythrodermic psoriasis" in f for f in r["urgentFlags"])


def test_pustular_generalized_urgent_flag():
    r = assess(_base(subtype="pustular_generalized"))
    assert any("Generalized pustular psoriasis" in f for f in r["urgentFlags"])


def test_active_tb_flag():
    r = assess(_base(hasActiveTuberculosis=True))
    assert any("ACTIVE TB" in f for f in r["urgentFlags"])


def test_chronic_hbv_flag():
    r = assess(_base(hasChronicHBV=True))
    assert any("Chronic HBV" in f for f in r["urgentFlags"])


# ---- Contraindications ----

def test_ibd_avoids_il17():
    r = assess(_base(hasInflammatoryBowelDisease=True))
    assert any("IL-17 inhibitors" in a for a in r["agentsToAvoid"])
    assert any("Brodalumab" in a for a in r["agentsToAvoid"])


def test_demyelinating_avoids_tnf():
    r = assess(_base(hasDemyelinatingDisease=True))
    assert any("contraindicated in demyelinating disease" in a for a in r["agentsToAvoid"])


def test_malignancy_avoids_tnf():
    r = assess(_base(hasMalignancyHistory=True))
    assert any("recent malignancy history" in a for a in r["agentsToAvoid"])


def test_pregnancy_avoids():
    r = assess(_base(isPregnant=True))
    assert any("Acitretin" in a for a in r["agentsToAvoid"])
    assert any("Methotrexate" in a for a in r["agentsToAvoid"])
    assert any("Most biologics" in a for a in r["agentsToAvoid"])


# ---- Moderate first-line branching ----

def test_moderate_prefers_oral():
    r = assess(_base(bsaPercent=5, prefersOralTherapy=True))
    assert any("Deucravacitinib" in a for a in r["firstLineAgents"])
    assert any("Apremilast 30mg BID" in a for a in r["firstLineAgents"])
    assert not any("Risankizumab" in a for a in r["firstLineAgents"])


def test_moderate_no_oral_preference():
    r = assess(_base(bsaPercent=5, prefersOralTherapy=False))
    assert any("Risankizumab" in a for a in r["firstLineAgents"])
    assert any("Bimekizumab" in a for a in r["firstLineAgents"])


def test_moderate_psa_notes():
    r = assess(_base(bsaPercent=5, hasPsoriaticArthritis=True))
    assert len(r["psoriaticArthritisNotes"]) == 4
    assert any("Rheumatology co-management" in n for n in r["psoriaticArthritisNotes"])


# ---- Severe first-line branching ----

def test_severe_ibd_branch():
    r = assess(_base(bsaPercent=15, hasInflammatoryBowelDisease=True))
    assert any("safe in IBD" in a for a in r["firstLineAgents"])
    assert any("treat both psoriasis and IBD" in a for a in r["firstLineAgents"])


def test_severe_psa_branch():
    r = assess(_base(bsaPercent=15, hasPsoriaticArthritis=True))
    assert any("highest skin clearance + PsA efficacy" in a for a in r["firstLineAgents"])


def test_severe_default_branch():
    r = assess(_base(bsaPercent=15))
    assert any("highest PASI 90/100 rates" in a for a in r["firstLineAgents"])
    assert any("Ustekinumab" in a for a in r["alternativeAgents"])


def test_severe_oral_adds_deucravacitinib_and_apremilast_alt():
    r = assess(_base(bsaPercent=15, prefersOralTherapy=True))
    assert any("oral TYK2 inhibitor" in a for a in r["firstLineAgents"])
    assert any("less effective for severe disease" in a for a in r["alternativeAgents"])


def test_severe_erythrodermic_adds_cyclosporine():
    r = assess(_base(subtype="erythrodermic"))
    assert any("Cyclosporine 3-5mg/kg/day" in a for a in r["firstLineAgents"])
    assert any("Infliximab 5mg/kg IV" in a for a in r["firstLineAgents"])


# ---- Special site management ----

def test_scalp_management():
    r = assess(_base(specialSites=["scalp"]))
    assert any("Scalp: Roflumilast" in s for s in r["specialSiteManagement"])
    assert len([s for s in r["specialSiteManagement"] if s.startswith("Scalp")]) == 3


def test_nails_management():
    r = assess(_base(specialSites=["nails"]))
    assert any(s.startswith("Nails:") for s in r["specialSiteManagement"])


def test_intertriginous_or_genitalia():
    r = assess(_base(specialSites=["genitalia"]))
    assert any("Intertriginous/genital: Roflumilast" in s for s in r["specialSiteManagement"])


# ---- Obesity / metabolic ----

def test_obesity_shared_decision_points():
    r = assess(_base(hasObesity=True))
    assert any("GLP-1 receptor agonists" in s for s in r["sharedDecisionPoints"])


def test_metabolic_syndrome_shared_decision_points():
    r = assess(_base(hasMetabolicSyndrome=True))
    assert any("Weight loss improves psoriasis severity" in s for s in r["sharedDecisionPoints"])


# ---- Always-present content ----

def test_monitoring_and_next_steps_and_refs():
    r = assess(_base())
    assert len(r["monitoringPlan"]) == 6
    assert len(r["nextSteps"]) == 4
    # 4 base shared decision points (no obesity)
    assert len(r["sharedDecisionPoints"]) == 4
    assert len(r["references"]) == 5
    assert r["references"][0]["pmid"] == "30772097"
    assert r["evidenceLevel"] == "Strong recommendation (AAD-NPF 2019/2026, Level A)"
