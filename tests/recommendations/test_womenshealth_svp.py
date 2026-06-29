"""Ported 1:1 from old_static_code/server/svp-classification.test.ts and
svp-ceap-treatment.test.ts.

The TypeScript oracle uses nested AssessmentData; the ported engine reads the
interface leaf fields flat, so fixtures are flattened equivalents.
"""

import re

from app.recommendations.modules.womenshealth import (
    assess,
    compute_ceap_classification,
    compute_svp_classification,
    compute_svp_treatment,
)


def make_assessment(**overrides) -> dict:
    """Flat equivalent of the TS makeAssessment() default AssessmentData."""
    base = {
        "chronicPelvicPain": False,
        "painDuration": "",
        "painLocation": "",
        "exacerbatedByStanding": False,
        "postcoitalPain": False,
        "premenstrualWorsening": False,
        "vulvarVaricosities": False,
        "gravidity": "",
        "parity": "",
        "lovDiameter": "",
        "rovDiameter": "",
        "lovRefluxDuration": "",
        "rovRefluxDuration": "",
        "crossPelvicFlow": "",
        "nutcrackerAngle": "",
        "pelvicVaricosities": False,
        "uterineVeinDilation": False,
        "dilatedArcuateVeins": "",
        "mayThurner": False,
    }
    base.update(overrides)
    return base


# ─── SVP Classification ───────────────────────────────────────────────────────


def test_asymptomatic_no_findings():
    r = compute_svp_classification(make_assessment())
    assert r["symptoms"] == 0
    assert r["varices"] == 0
    assert r["anatomic"] == 0
    assert r["hemodynamic"] == 0
    assert r["etiologic"] == "En"
    assert r["designation"] == "S0 V0 P(A0, H0, En)"
    assert "No significant pelvic venous disease" in r["interpretation"]


def test_s1_mild_single_symptom():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="6", painLocation="bilateral",
        gravidity="1", parity="1",
    ))
    assert r["symptoms"] == 1
    assert "Mild" in r["symptomsDescription"]


def test_s2_moderate():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="12", painLocation="bilateral",
        exacerbatedByStanding=True, gravidity="2", parity="2",
    ))
    assert r["symptoms"] == 2
    assert "Moderate" in r["symptomsDescription"]


def test_s3_severe():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="24", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, premenstrualWorsening=True,
        vulvarVaricosities=True, gravidity="3", parity="3",
    ))
    assert r["symptoms"] == 3
    assert "Severe" in r["symptomsDescription"]


def test_v1_pelvic_varices_only():
    r = compute_svp_classification(make_assessment(pelvicVaricosities=True))
    assert r["varices"] == 1
    assert "Pelvic varices only" in r["varicesDescription"]


def test_v2_perineal_vulvar_extension():
    r = compute_svp_classification(make_assessment(
        vulvarVaricosities=True, pelvicVaricosities=True,
    ))
    assert r["varices"] == 2
    assert "perineal/vulvar" in r["varicesDescription"]


def test_v3_lower_extremity_extension():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="12", painLocation="bilateral",
        exacerbatedByStanding=True, vulvarVaricosities=True, gravidity="2", parity="2",
        lovDiameter="7", lovRefluxDuration="2", crossPelvicFlow="present",
        pelvicVaricosities=True,
    ))
    assert r["varices"] == 3
    assert "lower extremities" in r["varicesDescription"]


def test_a1_gonadal_involvement():
    r = compute_svp_classification(make_assessment(lovDiameter="6"))
    assert r["anatomic"] == 1
    assert "Gonadal" in r["anatomicDescription"]


def test_a4_nutcracker():
    r = compute_svp_classification(make_assessment(
        lovDiameter="8", lovRefluxDuration="3", nutcrackerAngle="18",
    ))
    assert r["anatomic"] == 4
    assert "Nutcracker" in r["anatomicDescription"]


def test_a4_may_thurner():
    r = compute_svp_classification(make_assessment(mayThurner=True))
    assert r["anatomic"] == 4
    assert "May-Thurner" in r["anatomicDescription"]


def test_h1_reflux_only():
    r = compute_svp_classification(make_assessment(
        lovDiameter="6", lovRefluxDuration="2.5", nutcrackerAngle="45",
    ))
    assert r["hemodynamic"] == 1
    assert "Reflux only" in r["hemodynamicDescription"]


def test_h3_combined_reflux_obstruction():
    r = compute_svp_classification(make_assessment(
        lovDiameter="8", lovRefluxDuration="3", nutcrackerAngle="15",
    ))
    assert r["hemodynamic"] == 3
    assert "Combined reflux + obstruction" in r["hemodynamicDescription"]


def test_es_secondary_compression():
    r = compute_svp_classification(make_assessment(mayThurner=True))
    assert r["etiologic"] == "Es"
    assert "Secondary" in r["etiologicDescription"]


def test_ep_primary_gonadal_reflux():
    r = compute_svp_classification(make_assessment(
        lovDiameter="7", lovRefluxDuration="2", nutcrackerAngle="45",
    ))
    assert r["etiologic"] == "Ep"
    assert "Primary" in r["etiologicDescription"]


def test_designation_string_format():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="12", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, vulvarVaricosities=True,
        gravidity="2", parity="2", lovDiameter="7", lovRefluxDuration="2.5",
        crossPelvicFlow="present", nutcrackerAngle="45", pelvicVaricosities=True,
    ))
    assert re.match(r"^S\d V\d P\(A\d, H\d, E[psn]\)$", r["designation"])


def test_severe_symptomatic_interpretation_mentions_intervention_and_ceap():
    r = compute_svp_classification(make_assessment(
        chronicPelvicPain=True, painDuration="24", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, premenstrualWorsening=True,
        vulvarVaricosities=True, gravidity="3", parity="3", lovDiameter="8",
        lovRefluxDuration="3", crossPelvicFlow="present", nutcrackerAngle="45",
        pelvicVaricosities=True, uterineVeinDilation=True, dilatedArcuateVeins="pronounced",
    ))
    assert r["symptoms"] == 3
    assert r["varices"] == 3
    assert r["hemodynamic"] >= 1
    assert "Intervention is likely indicated" in r["interpretation"]
    assert "CEAP" in r["interpretation"]


# ─── assess() includes SVP classification ─────────────────────────────────────


def test_assess_returns_svp_classification():
    r = assess(make_assessment(
        chronicPelvicPain=True, painDuration="12", painLocation="left",
        exacerbatedByStanding=True, gravidity="2", parity="2",
        lovDiameter="6", lovRefluxDuration="2", nutcrackerAngle="45",
        pelvicVaricosities=True,
    ))
    svp = r["svpClassification"]
    assert svp["designation"]
    assert svp["symptoms"] >= 0
    assert svp["varices"] >= 0
    assert svp["anatomic"] >= 0
    assert svp["hemodynamic"] >= 0
    assert svp["etiologic"] in ("Ep", "Es", "Ec", "En")
    assert svp["interpretation"]


def test_assess_svp_consistent_with_direct_call():
    data = make_assessment(
        chronicPelvicPain=True, painDuration="18", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, vulvarVaricosities=True,
        gravidity="3", parity="2", lovDiameter="7", rovDiameter="4",
        lovRefluxDuration="2.5", rovRefluxDuration="0.5", crossPelvicFlow="present",
        nutcrackerAngle="40", pelvicVaricosities=True, uterineVeinDilation=True,
        dilatedArcuateVeins="mild",
    )
    direct = compute_svp_classification(data)
    via = assess(data)["svpClassification"]
    assert via["designation"] == direct["designation"]
    assert via["symptoms"] == direct["symptoms"]
    assert via["varices"] == direct["varices"]
    assert via["anatomic"] == direct["anatomic"]
    assert via["hemodynamic"] == direct["hemodynamic"]
    assert via["etiologic"] == direct["etiologic"]


# ─── CEAP Classification ──────────────────────────────────────────────────────


def test_ceap_c0_primary():
    r = compute_ceap_classification(
        {"clinicalClass": 0, "etiology": "Ep", "anatomy": "As", "pathophysiology": "Pr"}
    )
    assert r["designation"] == "C0,Ep,As,Pr"
    assert "No visible" in r["clinicalDescription"]
    assert "Primary" in r["etiologyDescription"]
    assert "Superficial" in r["anatomyDescription"]
    assert "Reflux" in r["pathophysiologyDescription"]


def test_ceap_c6_secondary():
    r = compute_ceap_classification(
        {"clinicalClass": 6, "etiology": "Es", "anatomy": "Ad", "pathophysiology": "Po"}
    )
    assert r["designation"] == "C6,Es,Ad,Po"
    assert "Active venous ulcer" in r["clinicalDescription"]
    assert "Secondary" in r["etiologyDescription"]
    assert "Deep" in r["anatomyDescription"]
    assert "Obstruction" in r["pathophysiologyDescription"]


def test_ceap_c3_congenital():
    r = compute_ceap_classification(
        {"clinicalClass": 3, "etiology": "Ec", "anatomy": "Ap", "pathophysiology": "Pr,o"}
    )
    assert r["designation"] == "C3,Ec,Ap,Pr,o"
    assert "Edema" in r["clinicalDescription"]
    assert "Congenital" in r["etiologyDescription"]
    assert "Perforator" in r["anatomyDescription"]
    assert "Reflux and obstruction" in r["pathophysiologyDescription"]


def test_ceap_combined_interpretation_present():
    r = compute_ceap_classification(
        {"clinicalClass": 4, "etiology": "Ep", "anatomy": "As", "pathophysiology": "Pr"}
    )
    assert r["combinedInterpretation"]
    assert len(r["combinedInterpretation"]) > 20


def test_ceap_en_pn():
    r = compute_ceap_classification(
        {"clinicalClass": 1, "etiology": "En", "anatomy": "An", "pathophysiology": "Pn"}
    )
    assert r["designation"] == "C1,En,An,Pn"
    assert "No identifiable" in r["etiologyDescription"]
    assert "No venous location" in r["anatomyDescription"]
    assert "No venous pathophysiology" in r["pathophysiologyDescription"]


# ─── SVP Treatment Algorithm ──────────────────────────────────────────────────


def _svp(symptoms, varices, anatomic, hemodynamic, etiologic):
    return {
        "symptoms": symptoms, "varices": varices, "anatomic": anatomic,
        "hemodynamic": hemodynamic, "etiologic": etiologic,
        "designation": f"S{symptoms} V{varices} P(A{anatomic}, H{hemodynamic}, {etiologic})",
        "interpretation": "test", "symptomsDescription": "desc", "varicesDescription": "desc",
        "anatomicDescription": "desc", "hemodynamicDescription": "desc", "etiologicDescription": "desc",
    }


def test_treatment_conservative_low():
    r = compute_svp_treatment(_svp(1, 0, 1, 0, "Ep"))
    assert r["tier"] == "conservative"
    assert "Conservative" in r["tierLabel"]
    assert r["primaryRecommendation"]
    assert r["followUpInterval"]


def test_treatment_diagnostic_or_definitive_moderate():
    r = compute_svp_treatment(_svp(2, 1, 2, 1, "Ep"))
    assert r["tier"] in ("diagnostic", "definitive")
    assert len(r["procedures"]) > 0


def test_treatment_definitive_high():
    r = compute_svp_treatment(_svp(3, 3, 3, 3, "Es"))
    assert r["tier"] == "definitive"
    assert "Definitive" in r["tierLabel"]
    assert len(r["procedures"]) > 0
    assert any("embolization" in p["name"].lower() for p in r["procedures"])


def test_treatment_surveillance_asymptomatic():
    r = compute_svp_treatment(_svp(0, 0, 0, 0, "En"))
    assert r["tier"] == "surveillance"
    assert "Surveillance" in r["tierLabel"]
    assert r["followUpInterval"]


def test_treatment_secondary_etiology_tier():
    r = compute_svp_treatment(_svp(2, 2, 2, 2, "Es"))
    assert r["tier"] in ("diagnostic", "definitive")
    assert r["primaryRecommendation"]


def test_treatment_adjunctive_for_moderate():
    r = compute_svp_treatment(_svp(2, 2, 2, 2, "Ep"))
    assert len(r["adjunctiveTherapies"]) > 0


def test_treatment_incorporates_ceap():
    svp = _svp(3, 3, 3, 2, "Ep")
    ceap = compute_ceap_classification(
        {"clinicalClass": 4, "etiology": "Ep", "anatomy": "As", "pathophysiology": "Pr"}
    )
    r = compute_svp_treatment(svp, ceap)
    assert (
        any("lower extremity" in s.lower() or "ceap" in s.lower() for s in r["specialConsiderations"])
        or any("compression" in t.lower() or "lower extremity" in t.lower() for t in r["adjunctiveTherapies"])
    )


def test_treatment_embolization_for_s2v2h1():
    r = compute_svp_treatment(_svp(2, 2, 2, 1, "Ep"))
    assert r["tier"] in ("diagnostic", "definitive")
    assert len(r["procedures"]) > 0


# ─── assess() includes SVP treatment ──────────────────────────────────────────


def test_assess_includes_svp_treatment():
    r = assess(make_assessment(
        chronicPelvicPain=True, painDuration=">6months", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, premenstrualWorsening=True,
        vulvarVaricosities=True, gravidity="3", parity="2",
        lovDiameter="9", rovDiameter="7", lovRefluxDuration="2", rovRefluxDuration="1.5",
        crossPelvicFlow="present", nutcrackerAngle="25",
        pelvicVaricosities=True, uterineVeinDilation=True, dilatedArcuateVeins="pronounced",
    ))
    tx = r["svpTreatment"]
    assert tx["tier"]
    assert tx["tierLabel"]
    assert tx["primaryRecommendation"]
    assert tx["followUpInterval"]
    assert isinstance(tx["procedures"], list)
    assert isinstance(tx["adjunctiveTherapies"], list)
    assert isinstance(tx["specialConsiderations"], list)


def test_assess_definitive_for_high_scoring():
    r = assess(make_assessment(
        chronicPelvicPain=True, painDuration=">6months", painLocation="bilateral",
        exacerbatedByStanding=True, postcoitalPain=True, premenstrualWorsening=True,
        vulvarVaricosities=True, gravidity="4", parity="3",
        lovDiameter="12", rovDiameter="10", lovRefluxDuration="3", rovRefluxDuration="2.5",
        crossPelvicFlow="present", nutcrackerAngle="20",
        pelvicVaricosities=True, uterineVeinDilation=True, dilatedArcuateVeins="pronounced",
        mayThurner=True,
    ))
    assert r["svpTreatment"]["tier"] == "definitive"
    assert any("embolization" in p["name"].lower() for p in r["svpTreatment"]["procedures"])


def test_assess_conservative_or_surveillance_minimal():
    r = assess(make_assessment(
        chronicPelvicPain=True, painDuration="<6months", painLocation="unilateral",
        gravidity="1", parity="0",
        lovDiameter="5", rovDiameter="4", lovRefluxDuration="0.5", rovRefluxDuration="0",
        crossPelvicFlow="absent", nutcrackerAngle="45",
    ))
    assert r["svpTreatment"]["tier"] in ("conservative", "surveillance")
