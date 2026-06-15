"""Tests for the Pancreatic Mass Evaluation engine.

No TypeScript test oracle exists for pancreaticMassLogic.ts, so these fixtures
are authored from the TS branches: each major decision path (solid mass workup,
cystic IPMN high-risk / worrisome, MCN, serous, pseudocyst, resectability tiers)
plus urgent-flag and edge paths.
"""

from app.recommendations.modules.pancreaticmass import assess


def _base(**overrides) -> dict:
    data = {
        "massType": "solid_mass",
        "massLocation": "head",
        "massSizeCm": None,
        "hasMainPancreaticDuctDilation": False,
        "mainPDDiameterMm": None,
        "hasSolidComponent": True,
        "hasEnhancingMuralNodule": False,
        "hasBileDuctDilation": False,
        "hasVascularInvolvement": False,
        "hasLymphadenopathy": False,
        "hasDistantMetastases": False,
        "hasJaundice": False,
        "hasWeightLoss": False,
        "hasAbdominalPain": False,
        "hasNewOnsetDiabetes": False,
        "hasAcutePancreatitis": False,
        "hasChronicPancreatitis": False,
        "ca199": None,
        "cea": None,
        "igg4": None,
        "hasCTScan": False,
        "hasMRIPancreas": False,
        "hasERCP": False,
        "hasEUSPerformed": False,
        "eusFindingsDescription": None,
        "hasTissueAcquired": False,
        "tissueResult": None,
        "cysticType": "unknown_cystic",
        "cystSizeCm": None,
        "hasWorrisomeFeatures": False,
        "hasHighRiskStigmata": False,
        "resectabilityStatus": "not_assessed",
        "hasSMAInvolvement": False,
        "hasCeliacInvolvement": False,
        "hasSMVPVInvolvement": False,
        "ageYears": 65,
        "performanceStatus": "good",
        "isSurgicalCandidate": True,
    }
    data.update(overrides)
    return data


def test_solid_mass_no_imaging_no_tissue_default():
    result = assess(_base())
    assert result["primaryRecommendation"].startswith(
        "Solid pancreatic mass: EUS-FNB"
    )
    # No prior imaging -> imaging required workup
    assert result["diagnosticWorkup"].startswith("IMAGING REQUIRED before EUS")
    # Solid mass EUS strategy
    assert result["eusStrategy"].startswith("EUS-GUIDED TISSUE ACQUISITION")
    # No tissue acquired -> acquisition strategy
    assert result["tissueAcquisitionApproach"].startswith(
        "TISSUE ACQUISITION STRATEGY"
    )
    assert result["cysticLesionManagement"] == "Not applicable — solid mass."
    assert result["evidenceLevel"] == "B"
    assert len(result["references"]) == 4


def test_high_risk_stigmata_takes_priority():
    result = assess(_base(massType="cystic_lesion", hasHighRiskStigmata=True))
    assert result["primaryRecommendation"].startswith("HIGH-RISK IPMN")
    flags = " ".join(result["urgentFlags"])
    assert "HIGH-RISK IPMN STIGMATA" in flags
    assert result["cysticLesionManagement"].startswith("HIGH-RISK IPMN STIGMATA")


def test_distant_metastases_flag_and_primary():
    result = assess(_base(hasDistantMetastases=True))
    assert result["primaryRecommendation"].startswith(
        "Metastatic pancreatic cancer"
    )
    assert any("Distant metastases" in f for f in result["urgentFlags"])


def test_ca199_over_1000_urgent_flag():
    result = assess(_base(ca199=1500))
    assert any("CA 19-9 1500 U/mL (>1000)" in f for f in result["urgentFlags"])


def test_ca199_at_1000_no_flag():
    # strictly greater than 1000
    result = assess(_base(ca199=1000))
    assert not any("CA 19-9" in f for f in result["urgentFlags"])


def test_ca199_none_no_flag():
    result = assess(_base(ca199=None))
    assert not any("CA 19-9" in f for f in result["urgentFlags"])


def test_new_onset_diabetes_over_50_solid_mass_flag():
    result = assess(_base(hasNewOnsetDiabetes=True, ageYears=60))
    assert any("New-onset diabetes" in f for f in result["urgentFlags"])


def test_new_onset_diabetes_age_50_no_flag():
    # age must be strictly > 50
    result = assess(_base(hasNewOnsetDiabetes=True, ageYears=50))
    assert not any("New-onset diabetes" in f for f in result["urgentFlags"])


def test_obstructive_jaundice_flag():
    result = assess(_base(hasJaundice=True, hasBileDuctDilation=True))
    assert any("OBSTRUCTIVE JAUNDICE" in f for f in result["urgentFlags"])


def test_ct_only_cystic_lesion_recommends_mri():
    result = assess(
        _base(massType="cystic_lesion", hasCTScan=True, hasMRIPancreas=False)
    )
    assert result["diagnosticWorkup"].startswith("MRI/MRCP recommended")
    assert "MRI/MRCP for cystic lesion characterization" in result["nextSteps"]


def test_imaging_performed_proceeds_to_eus():
    result = assess(_base(hasCTScan=True, hasMRIPancreas=True))
    assert result["diagnosticWorkup"].startswith(
        "Cross-sectional imaging performed"
    )


def test_cystic_lesion_eus_strategy():
    result = assess(_base(massType="cystic_lesion"))
    assert result["eusStrategy"].startswith("EUS for cystic pancreatic lesion")


def test_worrisome_features_management():
    result = assess(
        _base(massType="cystic_lesion", hasWorrisomeFeatures=True)
    )
    assert result["cysticLesionManagement"].startswith("WORRISOME IPMN FEATURES")


def test_mucinous_cystic_neoplasm_management():
    result = assess(
        _base(massType="cystic_lesion", cysticType="mucinous_cystic_neoplasm")
    )
    assert result["cysticLesionManagement"].startswith(
        "MUCINOUS CYSTIC NEOPLASM (MCN)"
    )


def test_serous_cystadenoma_surveillance():
    result = assess(
        _base(massType="cystic_lesion", cysticType="serous_cystadenoma")
    )
    assert result["cysticLesionManagement"].startswith("SEROUS CYSTADENOMA")
    # benign cystic w/o high-risk/worrisome -> surveillance primary rec
    assert result["primaryRecommendation"].startswith(
        "Cystic pancreatic lesion without high-risk features"
    )


def test_pseudocyst_management():
    result = assess(
        _base(massType="cystic_lesion", cysticType="pseudocyst")
    )
    assert result["cysticLesionManagement"].startswith("PANCREATIC PSEUDOCYST")


def test_uncertain_cystic_type_management():
    result = assess(
        _base(massType="cystic_lesion", cysticType="unknown_cystic")
    )
    assert result["cysticLesionManagement"].startswith(
        "Cystic lesion of uncertain type"
    )


def test_resectable_solid_mass():
    result = assess(_base(resectabilityStatus="resectable"))
    assert result["resectabilityAssessment"].startswith("RESECTABLE")


def test_borderline_resectable():
    result = assess(_base(resectabilityStatus="borderline_resectable"))
    assert result["resectabilityAssessment"].startswith("BORDERLINE RESECTABLE")


def test_locally_advanced():
    result = assess(_base(resectabilityStatus="locally_advanced"))
    assert result["resectabilityAssessment"].startswith("LOCALLY ADVANCED")


def test_metastatic_resectability():
    result = assess(_base(resectabilityStatus="metastatic"))
    assert result["resectabilityAssessment"].startswith("METASTATIC")


def test_resectability_not_assessed():
    result = assess(_base(resectabilityStatus="not_assessed"))
    assert result["resectabilityAssessment"].startswith(
        "Resectability not yet assessed"
    )


def test_cystic_lesion_no_solid_no_resectability_assessment():
    # cystic lesion that is not malignant tissue -> resectability block skipped
    result = assess(
        _base(massType="cystic_lesion", resectabilityStatus="resectable")
    )
    assert result["resectabilityAssessment"] == ""


def test_malignant_tissue_triggers_resectability_even_if_not_solid():
    result = assess(
        _base(
            massType="cystic_lesion",
            hasTissueAcquired=True,
            tissueResult="malignant",
            resectabilityStatus="resectable",
        )
    )
    assert result["resectabilityAssessment"].startswith("RESECTABLE")


def test_non_diagnostic_tissue_approach():
    result = assess(
        _base(hasTissueAcquired=True, tissueResult="non_diagnostic")
    )
    assert result["tissueAcquisitionApproach"].startswith(
        "Non-diagnostic prior tissue acquisition"
    )
    assert "Repeat EUS-FNB with alternative needle type" in result["nextSteps"]


def test_tissue_acquired_result_interpolated():
    result = assess(
        _base(hasTissueAcquired=True, tissueResult="benign")
    )
    assert result["tissueAcquisitionApproach"] == (
        "Tissue acquired — result: benign. Proceed with management based on "
        "pathology."
    )


def test_rationale_replaces_underscores_and_size():
    result = assess(
        _base(
            massType="mixed_solid_cystic",
            massLocation="body",
            massSizeCm=3,
            cysticType="ipmn_branch_duct",
            resectabilityStatus="borderline_resectable",
        )
    )
    r = result["rationale"]
    assert "Mass type: mixed solid cystic." in r
    assert "Location: body." in r
    assert "Size: 3cm." in r
    assert "Cystic type: ipmn branch duct." in r
    assert "Resectability: borderline resectable." in r


def test_rationale_size_not_measured_when_zero_or_missing():
    result = assess(_base(massSizeCm=None))
    assert "Size: not measured." in result["rationale"]
    result0 = assess(_base(massSizeCm=0))
    assert "Size: not measured." in result0["rationale"]


def test_rationale_tissue_acquired_yes_with_result():
    result = assess(
        _base(hasTissueAcquired=True, tissueResult="suspicious")
    )
    assert "Tissue acquired: Yes (suspicious)." in result["rationale"]


def test_default_next_steps_when_none_added():
    # imaging done, tissue acquired+diagnostic, cystic-not, resectability assessed
    # path that adds no next steps -> fallback list populates
    result = assess(
        _base(
            massType="ductal_dilation_only",
            hasCTScan=True,
            hasMRIPancreas=True,
            hasTissueAcquired=True,
            tissueResult="benign",
        )
    )
    assert "EUS-FNB for tissue acquisition" in result["nextSteps"]
    assert len(result["nextSteps"]) == 6
