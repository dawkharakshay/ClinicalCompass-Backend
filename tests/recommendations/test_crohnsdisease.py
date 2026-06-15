"""Tests for the Crohn's Disease module, ported from the TS branches of
old_static_code/client/src/lib/crohnsDiseaseLogic.ts (no TS test exists).

Fixtures cover each major decision path: top-down (perianal/colonic/ileal),
step-up, anti-TNF failure, multiple biologic failure, optimize-current, plus
contraindication flags and the surgical-consideration branches.
"""

from app.recommendations.modules.crohnsdisease import assess


def _base(**overrides):
    data = {
        "location": "ileal",
        "pattern": "inflammatory",
        "severity": "mild",
        "hasPerianaldisease": False,
        "hasFistula": False,
        "hasAbscess": False,
        "hasStricture": False,
        "hasPenetrating": False,
        "crpStatus": "normal",
        "endoscopicActivity": "mild",
        "hasDeepUlcers": False,
        "hasExtensiveDisease": False,
        "priorTherapy": "none",
        "hasLostResponseToBiologic": False,
        "hasAntiDrugAntibodies": False,
        "hasSmoking": False,
        "hasPerinealDisease": False,
        "hasUpperGIInvolvement": False,
        "hasGrowthFailure": False,
        "hasPreviousSurgery": False,
        "hasExtraintestinalManifestations": False,
        "hasActiveTB": False,
        "hasLatentTB": False,
        "hasHepatitisB": False,
        "hasMalignancyHistory": False,
        "hasDemyelinatingDisease": False,
        "hasCongestiveHeartFailure": False,
        "isPregnantOrPlanning": False,
        "hasJAKContraindication": False,
        "wantsTopDown": False,
        "prefersOralTherapy": False,
        "prefersSubcutaneous": False,
    }
    data.update(overrides)
    return data


def test_step_up_low_risk_mild():
    r = assess(_base(severity="mild"))
    assert "step-up approach acceptable" in r["treatmentStrategy"]
    assert r["biologicSelection"] == ""
    assert r["recommendedAgents"][0].startswith("Budesonide 9mg/day")
    assert r["primaryRecommendation"].startswith("Mild Crohn's disease")
    assert r["surgicalConsideration"].startswith("No immediate surgical indication")
    # No perianal/penetrating/stricturing -> default nextSteps
    assert r["nextSteps"][0].startswith("Baseline labs")
    assert r["perianaldiseasePlan"] == "No perianal disease identified."
    assert r["evidenceLevel"] == "A"
    assert len(r["references"]) == 6


def test_top_down_moderate_ileal():
    r = assess(_base(severity="moderate"))
    assert r["treatmentStrategy"].startswith("TOP-DOWN STRATEGY RECOMMENDED")
    assert r["biologicSelection"].startswith("Ileal/ileocolonic Crohn's")
    assert r["recommendedAgents"][0].startswith("Risankizumab 600mg IV x3")
    assert r["primaryRecommendation"].startswith("Moderate-severe or high-risk")
    assert "early advanced therapy (top-down biologic) recommended" in r["primaryRecommendation"]


def test_top_down_perianal_fistula_first_line_anti_tnf():
    r = assess(_base(severity="moderate", hasPerianaldisease=True, hasFistula=True))
    assert r["biologicSelection"].startswith("Perianal/fistulizing Crohn's")
    assert r["recommendedAgents"][0].startswith("Infliximab 5mg/kg IV (induction + maintenance)")
    assert r["perianaldiseasePlan"].startswith("Perianal Crohn's management")
    assert r["nextSteps"][0] == "MRI pelvis to characterize perianal fistula anatomy"
    assert "Yes" in r["rationale"]


def test_top_down_colonic():
    r = assess(_base(severity="moderate", location="colonic"))
    assert r["biologicSelection"].startswith("Colonic Crohn's or prominent EIM")
    assert r["recommendedAgents"][0].startswith("Vedolizumab 300mg IV")


def test_top_down_eim_triggers_colonic_branch():
    r = assess(_base(severity="moderate", location="ileal", hasExtraintestinalManifestations=True))
    assert r["biologicSelection"].startswith("Colonic Crohn's or prominent EIM")


def test_high_risk_via_markers_in_mild():
    # 3 poor-prognosis markers -> high risk even when severity mild & not top-down
    r = assess(
        _base(
            severity="mild",
            hasSmoking=True,
            hasUpperGIInvolvement=True,
            hasPreviousSurgery=True,
        )
    )
    assert r["treatmentStrategy"].startswith("TOP-DOWN STRATEGY RECOMMENDED")
    assert "(3 poor prognosis markers)" in r["rationale"]
    assert "High risk: Yes" in r["rationale"]


def test_wants_top_down_overrides_step_up():
    r = assess(_base(severity="mild", wantsTopDown=True))
    assert r["treatmentStrategy"].startswith("TOP-DOWN STRATEGY RECOMMENDED")


def test_failed_anti_tnf():
    r = assess(_base(severity="moderate", priorTherapy="failed_anti_tnf"))
    assert r["treatmentStrategy"].startswith("Anti-TNF failure")
    assert r["biologicSelection"].startswith("Post-anti-TNF options")
    assert r["recommendedAgents"][0].startswith("Risankizumab 600mg IV x3 then 360mg SC Q8W (preferred")
    assert "escalate to next-line biologic/mechanism" in r["primaryRecommendation"]


def test_failed_multiple_biologics():
    r = assess(_base(severity="severe", priorTherapy="failed_multiple_biologics"))
    assert r["treatmentStrategy"].startswith("Multiple biologic failure")
    assert r["biologicSelection"].startswith("Refractory CD options")
    assert any("multidisciplinary IBD team review" in f for f in r["urgentFlags"])
    # surgical consideration -> refractory branch (no abscess/stricture/penetrating)
    assert r["surgicalConsideration"].startswith("Refractory disease")


def test_optimize_current_unknown_prior_therapy():
    r = assess(_base(severity="moderate", priorTherapy="failed_immunomodulator"))
    assert r["treatmentStrategy"].startswith("Optimize current therapy")
    assert r["recommendedAgents"] == [
        "Therapeutic drug monitoring (TDM) — check trough levels and antibodies before switching"
    ]


def test_abscess_urgent_and_surgical():
    r = assess(_base(severity="moderate", hasAbscess=True))
    assert r["urgentFlags"][0].startswith("ABSCESS:")
    assert r["surgicalConsideration"].startswith("Penetrating disease/abscess")
    assert r["perianaldiseasePlan"].startswith("Perianal Crohn's management")
    assert "Surgical consultation" in r["nextSteps"]


def test_stricturing_surgical_branch():
    r = assess(_base(severity="moderate", pattern="stricturing"))
    assert r["surgicalConsideration"].startswith("Stricturing disease")
    assert r["nextSteps"][0].startswith("MRI enterography")


def test_severe_markedly_elevated_crp_urgent():
    r = assess(_base(severity="severe", crpStatus="markedly_elevated"))
    assert any("markedly elevated CRP" in f for f in r["urgentFlags"])


def test_chf_contraindicates_anti_tnf():
    r = assess(_base(severity="moderate", hasCongestiveHeartFailure=True))
    assert any("CHF (EF <35%)" in f for f in r["urgentFlags"])
    assert any(a.startswith("Anti-TNF agents (infliximab") for a in r["agentsToAvoid"])


def test_active_tb_blocks_all_biologics():
    r = assess(_base(severity="severe", hasActiveTB=True))
    assert any("ACTIVE TB" in f for f in r["urgentFlags"])
    assert any("All biologics" in a for a in r["agentsToAvoid"])


def test_malignancy_and_jak_contraindication():
    r = assess(_base(severity="moderate", hasMalignancyHistory=True, hasJAKContraindication=True))
    avoid = r["agentsToAvoid"]
    assert any("relative contraindication with prior malignancy" in a for a in avoid)
    assert any("FDA Black Box Warning 2023" in a for a in avoid)


def test_age_at_diagnosis_under_30_counts_as_marker():
    r = assess(
        _base(
            severity="mild",
            ageAtDiagnosis=25,
            hasSmoking=True,
            hasPenetrating=True,
        )
    )
    # age<30, smoking, penetrating = 3 markers -> high risk
    assert "(3 poor prognosis markers)" in r["rationale"]
    assert r["treatmentStrategy"].startswith("TOP-DOWN STRATEGY RECOMMENDED")


def test_rationale_replaces_underscores():
    r = assess(_base(location="upper_gi", priorTherapy="on_steroids_only", severity="mild"))
    assert "CD location: upper gi." in r["rationale"]
    assert "Prior therapy: on steroids only." in r["rationale"]
