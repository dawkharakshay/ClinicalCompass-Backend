"""Parkinson's engine — fixtures derived directly from parkinsonsLogic.ts branches."""

from app.recommendations.modules.parkinsons import assess


def _base() -> dict:
    return {
        "stage": "early",
        "age": "55",
        "updrsMotorScore": "15",
        "hoehnYahrScale": "2",
        "motorFluctuations": "none",
        "initialTherapyHistory": "none",
        "tremorDominant": False,
        "hasHallucinations": False,
        "hasDementia": False,
        "hasOrthostasis": False,
        "hasImpulseControlDisorder": False,
        "hasCardiacHistory": False,
        "isDBSCandidate": False,
        "dbsContraindications": [],
        "wantsNonOralTherapy": False,
        "isPregnantOrPlanning": False,
    }


def test_early_young_non_tremor_dopamine_agonist():
    r = assess(_base())
    assert "age <65" in r["pharmacotherapy"]
    assert "Pramipexole ER 0.375–4.5mg/day" in r["recommendedAgents"]
    assert r["primaryRecommendation"].startswith("Early PD: dopamine agonist")
    # No motor fluctuation steps -> default next steps block.
    assert "Movement disorder specialist referral" in r["nextSteps"]
    assert "Driving safety evaluation" in r["nextSteps"]


def test_early_older_prefers_levodopa():
    r = assess({**_base(), "age": "70"})
    assert "age ≥65 or tremor-dominant" in r["pharmacotherapy"]
    assert "Levodopa-carbidopa 25/100mg TID (titrate to response)" in r["recommendedAgents"]
    assert "levodopa-carbidopa preferred (age ≥65)" in r["primaryRecommendation"]


def test_early_tremor_dominant_prefers_levodopa():
    r = assess({**_base(), "age": "50", "tremorDominant": True})
    assert "age ≥65 or tremor-dominant" in r["pharmacotherapy"]


def test_early_on_therapy_optimizes():
    r = assess({**_base(), "initialTherapyHistory": "on_levodopa"})
    assert "Established early PD on therapy" in r["pharmacotherapy"]
    assert "Optimize current therapy" in r["recommendedAgents"]


def test_wearing_off_branch():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "wearing_off"})
    assert r["pharmacotherapy"].startswith("Wearing-off fluctuations")
    assert "Opicapone 50mg once daily (COMT inhibitor)" in r["recommendedAgents"]
    assert "Wearing-off diary to quantify off-time" in r["nextSteps"]
    assert "Moderate PD with wearing off" in r["primaryRecommendation"]


def test_dyskinesia_branch_no_dementia_includes_amantadine():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "dyskinesia"})
    assert "Levodopa-induced dyskinesia" in r["pharmacotherapy"]
    assert "Amantadine 100mg BID–TID" in r["recommendedAgents"]
    assert "DBS evaluation (GPi target preferred for dyskinesia)" in r["recommendedAgents"]


def test_dyskinesia_branch_dementia_omits_amantadine():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "dyskinesia",
                "hasDementia": True})
    assert "Amantadine 100mg BID–TID" not in r["recommendedAgents"]
    assert "DBS evaluation (GPi target preferred for dyskinesia)" in r["recommendedAgents"]


def test_on_off_advanced_device_aided():
    r = assess({**_base(), "stage": "advanced", "motorFluctuations": "on_off"})
    assert "device-aided therapy should be considered" in r["pharmacotherapy"]
    assert "DBS evaluation (STN-DBS preferred for fluctuations)" in r["recommendedAgents"]
    assert "Off-time diary (hours/day)" in r["nextSteps"]


def test_advanced_stage_triggers_on_off_branch_even_without_fluctuation_match():
    # stage advanced + motorFluctuations not matching earlier branches -> on_off branch
    r = assess({**_base(), "stage": "advanced", "motorFluctuations": "freezing"})
    # freezing matches before on_off check? Order: wearing_off, dyskinesia,
    # (on_off OR advanced), freezing. advanced wins here.
    assert "device-aided therapy should be considered" in r["pharmacotherapy"]


def test_freezing_branch():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "freezing"})
    assert "Freezing of gait (FOG)" in r["pharmacotherapy"]
    assert "Anticholinergics (may worsen FOG and cognition)" in r["agentsToAvoid"]


def test_moderate_no_fluctuation_default_branch():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "none"})
    assert r["pharmacotherapy"].startswith("Moderate PD: optimize levodopa regimen")
    assert "Moderate PD: optimize pharmacotherapy" in r["primaryRecommendation"]


def test_dbs_candidate_meets_criteria():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "wearing_off",
                "updrsMotorScore": "25", "isDBSCandidate": True})
    assert r["dbsAssessment"].startswith("DBS CANDIDATE")
    assert "DBS evaluation referral (STN or GPi target)" in r["recommendedAgents"]
    assert "Psychiatric clearance" in r["nextSteps"]


def test_dbs_not_candidate_count_too_low():
    # early stage (criterion 1 false), no fluctuations (criterion 2 false),
    # updrs 15 (<20, criterion 5 false) -> only 2 criteria met -> not candidate.
    r = assess({**_base(), "isDBSCandidate": True})
    assert r["dbsAssessment"].startswith("DBS not currently indicated")


def test_dbs_contraindicated():
    r = assess({**_base(), "dbsContraindications": ["active psychiatric illness"],
                "wantsNonOralTherapy": True})
    assert r["dbsAssessment"].startswith("DBS contraindicated: active psychiatric illness")
    assert "Levodopa-carbidopa intestinal gel (LCIG/Duopa)" in r["recommendedAgents"]


def test_dbs_contraindicated_no_non_oral():
    r = assess({**_base(), "dbsContraindications": ["dementia"]})
    assert r["dbsAssessment"].startswith("DBS contraindicated: dementia")
    assert "Subcutaneous apomorphine infusion" not in r["recommendedAgents"]


def test_safety_flags_hallucinations():
    r = assess({**_base(), "hasHallucinations": True})
    assert any("Hallucinations present" in f for f in r["urgentFlags"])
    assert "Dopamine agonists (worsen psychosis)" in r["agentsToAvoid"]
    assert "MAO-B inhibitors (may worsen psychosis)" in r["agentsToAvoid"]


def test_safety_flags_icd():
    r = assess({**_base(), "hasImpulseControlDisorder": True})
    assert any("Impulse control disorder" in f for f in r["urgentFlags"])
    assert "Dopamine agonists (ICD risk — pramipexole, ropinirole, rotigotine)" in r["agentsToAvoid"]


def test_safety_flags_dementia_and_nonmotor():
    r = assess({**_base(), "hasDementia": True})
    assert any("Dementia present" in f for f in r["urgentFlags"])
    assert "Anticholinergics (worsen cognition)" in r["agentsToAvoid"]
    assert "Rivastigmine for PD dementia (AAN Level A)" in r["recommendedAgents"]
    assert "only FDA-approved agent for PD dementia" in r["nonMotorManagement"]


def test_safety_flags_orthostasis():
    r = assess({**_base(), "hasOrthostasis": True})
    assert any("Orthostatic hypotension" in f for f in r["urgentFlags"])
    assert "High-dose dopamine agonists (worsen orthostasis)" in r["agentsToAvoid"]


def test_evidence_level_and_references():
    r = assess(_base())
    assert r["evidenceLevel"] == "A"
    assert len(r["references"]) == 6
    assert r["references"][0]["pmid"] == "29570866"


def test_rationale_replaces_underscores():
    r = assess({**_base(), "stage": "moderate", "motorFluctuations": "wearing_off",
                "initialTherapyHistory": "on_dopamine_agonist"})
    assert "Motor fluctuations: wearing off." in r["rationale"]
    assert "Prior therapy: on dopamine agonist." in r["rationale"]
