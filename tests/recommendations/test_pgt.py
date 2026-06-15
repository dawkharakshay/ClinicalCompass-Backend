"""Tests for the PGT Clinical Compass port.

Oracle: old_static_code/client/src/pages/PGTCompass.tsx evaluate(). No
server-side *.test.ts existed; fixtures derived 1:1 from the TS branches.
"""

from app.recommendations.modules.pgt import assess


def test_pgt_m_known_disorder_indicated():
    r = assess({
        "pgtType": "pgt_m",
        "knownGeneticDisorder": True,
        "geneDisorderName": "cystic fibrosis",
    })
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "PGT-M (monogenic/single gene disorder)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert "cystic fibrosis" in r["rationale"][0]
    assert len(r["rationale"]) == 2
    assert r["warnings"] == []


def test_pgt_m_no_disorder_name_defaults_specified():
    r = assess({"pgtType": "pgt_m", "knownGeneticDisorder": True})
    assert r["recommendation"] == "indicated"
    assert "(specified)" in r["rationale"][0]


def test_pgt_sr_translocation_indicated():
    r = assess({"pgtType": "pgt_sr", "chromosomalTranslocation": True})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "PGT-SR (structural rearrangement — translocation)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"


def test_pgt_a_strong_indication_age():
    r = assess({"pgtType": "pgt_a", "femaleAge": 38})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "PGT-A (aneuploidy screening)"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"
    # femaleAge 38 -> no ".0" in interpolation
    assert any("Advanced maternal age (38)" in x for x in r["rationale"])
    assert len(r["warnings"]) == 1


def test_pgt_a_strong_indication_rpl():
    r = assess({
        "pgtType": "pgt_a",
        "recurrentPregnancyLoss": True,
        "rplCount": 3,
    })
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "IIa"
    assert any("Recurrent pregnancy loss (3 losses)" in x for x in r["rationale"])


def test_pgt_a_strong_indication_repeated_ivf():
    r = assess({
        "pgtType": "pgt_a",
        "repeatedIVFFailure": True,
        "ivfFailureCount": 2,
    })
    assert r["recommendation"] == "indicated"
    assert any("Repeated IVF failure (2 cycles)" in x for x in r["rationale"])


def test_pgt_a_prior_aneuploid_strong():
    r = assess({"pgtType": "pgt_a", "priorAneuploidPregnancy": True})
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "IIa"


def test_pgt_a_rpl_count_below_threshold_not_strong():
    # RPL true but only 1 loss, no other indication -> consider
    r = assess({
        "pgtType": "pgt_a",
        "recurrentPregnancyLoss": True,
        "rplCount": 1,
        "femaleAge": 30,
    })
    assert r["recommendation"] == "consider"
    assert r["procedure"] == "PGT-A — consider with shared decision-making"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"


def test_pgt_a_ivf_failure_below_threshold_not_strong():
    r = assess({
        "pgtType": "pgt_a",
        "repeatedIVFFailure": True,
        "ivfFailureCount": 1,
    })
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIb"


def test_pgt_a_no_indication_consider():
    r = assess({"pgtType": "pgt_a", "femaleAge": 30})
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"
    assert r["warnings"] == []


def test_pgt_m_without_known_disorder_falls_to_not_indicated():
    # pgt_m but no known disorder -> not pgt_a -> else branch
    r = assess({"pgtType": "pgt_m", "knownGeneticDisorder": False})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "PGT not indicated based on current inputs"
    assert r["cor"] == "I"
    assert r["loe"] == "B"


def test_pgt_sr_without_translocation_not_indicated():
    r = assess({"pgtType": "pgt_sr", "chromosomalTranslocation": False})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "PGT not indicated based on current inputs"


def test_sex_selection_warning_appended():
    r = assess({"pgtType": "pgt_a", "femaleAge": 40, "sexSelection": True})
    assert any("Non-medical sex selection" in w for w in r["warnings"])
    # strong indication warning + sex selection warning
    assert len(r["warnings"]) == 2


def test_sex_selection_warning_on_not_indicated():
    r = assess({"pgtType": "pgt_m", "knownGeneticDisorder": False, "sexSelection": True})
    assert r["recommendation"] == "not_indicated"
    assert len(r["warnings"]) == 1
    assert "Non-medical sex selection" in r["warnings"][0]


def test_references_always_present():
    r = assess({"pgtType": "pgt_a"})
    assert len(r["references"]) == 4
    assert r["references"][0].startswith("Practice Committee of the ASRM")


def test_string_inputs_coerced():
    # form submits strings for checkboxes/numbers
    r = assess({
        "pgtType": "pgt_a",
        "recurrentPregnancyLoss": "true",
        "rplCount": "2",
    })
    assert r["recommendation"] == "indicated"
    assert any("Recurrent pregnancy loss (2 losses)" in x for x in r["rationale"])
