"""Tests for the Vasectomy Reversal Clinical Compass port.

No dedicated *.test.ts oracle exists; fixtures are derived directly from the
branches of evaluate() in VasectomyReversalCompass.tsx.
"""

from app.recommendations.modules.vasectomyreversal import assess


def _base():
    return {
        "yearsSinceVasectomy": 0,
        "priorVasectomyReversal": False,
        "spermInVas": None,
        "partnerAge": 0,
        "antispermAntibodies": False,
        "epididymalObstruction": False,
        "testisVolume": "normal",
        "fshLevel": 0,
    }


def test_short_interval_prognosis_and_default_procedure():
    r = assess({**_base(), "yearsSinceVasectomy": 2})
    assert r["patencyRate"] == "97%"
    assert r["pregnancyRate"] == "76%"
    assert r["procedure"] == "Vasovasostomy (VV)"
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert r["warnings"] == []
    assert "Obstructive interval of 2 years" in r["rationale"][0]


def test_interval_boundaries():
    assert assess({**_base(), "yearsSinceVasectomy": 3})["patencyRate"] == "97%"
    assert assess({**_base(), "yearsSinceVasectomy": 8})["patencyRate"] == "88%"
    assert assess({**_base(), "yearsSinceVasectomy": 8})["pregnancyRate"] == "53%"
    assert assess({**_base(), "yearsSinceVasectomy": 14})["patencyRate"] == "79%"
    assert assess({**_base(), "yearsSinceVasectomy": 14})["pregnancyRate"] == "44%"


def test_long_interval_changes_cor():
    r = assess({**_base(), "yearsSinceVasectomy": 20})
    assert r["patencyRate"] == "71%"
    assert r["pregnancyRate"] == "30%"
    assert r["cor"] == "IIa"


def test_epididymal_obstruction_forces_ve():
    r = assess({**_base(), "yearsSinceVasectomy": 5, "epididymalObstruction": True})
    assert r["procedure"] == "Vasoepididymostomy (VE)"
    assert any("technically more demanding" in w for w in r["warnings"])
    assert r["rationale"][1] == (
        "Absence of sperm in vasal fluid or epididymal obstruction indicates vasoepididymostomy is required."
    )


def test_no_sperm_in_vas_forces_ve():
    r = assess({**_base(), "spermInVas": False})
    assert r["procedure"] == "Vasoepididymostomy (VE)"


def test_unknown_sperm_does_not_force_ve():
    # spermInVas === false is strict; None (unknown) must NOT trigger VE.
    r = assess({**_base(), "spermInVas": None})
    assert r["procedure"] == "Vasovasostomy (VV)"


def test_sperm_present_keeps_vv():
    r = assess({**_base(), "spermInVas": True})
    assert r["procedure"] == "Vasovasostomy (VV)"


def test_partner_age_over_37_warning():
    r = assess({**_base(), "partnerAge": 40})
    assert any("Partner age 40" in w and "diminished ovarian reserve" in w for w in r["warnings"])
    assert any("IVF/ICSI as alternative when female partner is >37" in x for x in r["rationale"])


def test_partner_age_37_no_warning():
    r = assess({**_base(), "partnerAge": 37})
    assert not any("diminished ovarian reserve" in w for w in r["warnings"])


def test_antisperm_antibodies_warning():
    r = assess({**_base(), "antispermAntibodies": True})
    assert any("Anti-sperm antibodies detected" in w for w in r["warnings"])


def test_fsh_elevated_warning():
    r = assess({**_base(), "fshLevel": 9.0})
    assert any("Elevated FSH (9 mIU/mL)" in w for w in r["warnings"])


def test_fsh_boundary_no_warning():
    r = assess({**_base(), "fshLevel": 7.6})
    assert not any("Elevated FSH" in w for w in r["warnings"])


def test_atrophic_testis_triggers_caution():
    r = assess({**_base(), "testisVolume": "atrophic"})
    assert r["recommendation"] == "caution"
    assert any("Testicular atrophy" in w for w in r["warnings"])
    assert any("poor reversal outcomes" in x for x in r["rationale"])


def test_reduced_testis_not_caution():
    r = assess({**_base(), "testisVolume": "reduced"})
    assert r["recommendation"] == "indicated"


def test_elevated_fsh_alone_not_caution():
    # FSH warning says "spermatogenic impairment" not "spermatogenic failure".
    r = assess({**_base(), "fshLevel": 9.0})
    assert r["recommendation"] == "indicated"


def test_prior_reversal_warning():
    r = assess({**_base(), "priorVasectomyReversal": True})
    assert any("Prior failed reversal" in w for w in r["warnings"])


def test_string_inputs_coerced():
    r = assess({
        **_base(),
        "yearsSinceVasectomy": "5",
        "partnerAge": "40",
        "fshLevel": "8.0",
        "priorVasectomyReversal": "true",
        "antispermAntibodies": "yes",
        "epididymalObstruction": "no",
        "spermInVas": "no",
    })
    assert r["patencyRate"] == "88%"
    assert r["procedure"] == "Vasoepididymostomy (VE)"  # spermInVas "no" -> False
    assert any("Partner age 40" in w for w in r["warnings"])
    assert any("Elevated FSH (8 mIU/mL)" in w for w in r["warnings"])
    assert any("Prior failed reversal" in w for w in r["warnings"])


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 5
    assert r["references"][0].startswith("Belker AM")
