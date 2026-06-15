"""Embryo Cryopreservation engine — fixtures derived from EmbryoCryoCompass.tsx evaluate()."""

from app.recommendations.modules import embryocryo
from app.recommendations.modules.embryocryo import assess

_STORAGE_FEE = (
    "Annual embryo storage fees (CPT 89344) are almost universally excluded "
    "from insurance coverage. Patients should budget for self-pay storage "
    "costs ($500–$1,000/year)."
)


def _base() -> dict:
    return {
        "indication": "ivf_excess",
        "gonadotoxicTherapy": False,
        "ovarianHyperstimulationRisk": False,
        "endometrialIssue": False,
        "pgtPlanned": False,
        "excessEmbryos": False,
        "embryoCount": 0,
        "singleEmbryo": False,
        "storageYears": 0,
    }


def test_logic_key():
    assert embryocryo.LOGIC_KEY == "embryocryo"


def test_oncofertility_with_gonadotoxic_is_class_i_a():
    r = assess({**_base(), "indication": "oncofertility", "gonadotoxicTherapy": True})
    assert r["procedure"] == "Embryo cryopreservation — oncofertility (medical necessity)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("ASCO 2018" in x for x in r["rationale"])
    assert any("highest success rates" in x for x in r["rationale"])
    # only the universal storage-fee warning
    assert r["warnings"] == [_STORAGE_FEE]


def test_oncofertility_without_gonadotoxic_falls_through_to_donor():
    # In TS, oncofertility without gonadotoxicTherapy matches no branch and
    # hits the final else (donor banking).
    r = assess({**_base(), "indication": "oncofertility", "gonadotoxicTherapy": False})
    assert r["procedure"] == "Embryo cryopreservation — donor embryo banking"
    assert r["cor"] == "I"
    assert r["loe"] == "B"


def test_ivf_excess_baseline():
    r = assess(_base())
    assert r["procedure"] == "Embryo cryopreservation — excess embryos from IVF cycle"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert len(r["rationale"]) == 1
    assert r["warnings"] == [_STORAGE_FEE]


def test_ivf_excess_with_ohss_adds_freeze_all_warning():
    r = assess({**_base(), "ovarianHyperstimulationRisk": True})
    assert any("OHSS risk" in x for x in r["rationale"])
    assert any("Freeze-all strategy recommended" in w for w in r["warnings"])
    # freeze-all warning ordered before the universal fee warning
    assert r["warnings"][-1] == _STORAGE_FEE


def test_ivf_excess_with_endometrial_issue():
    r = assess({**_base(), "endometrialIssue": True})
    assert any("Endometrial issue identified" in x for x in r["rationale"])


def test_ivf_excess_ohss_and_endometrial_order():
    r = assess({**_base(), "ovarianHyperstimulationRisk": True, "endometrialIssue": True})
    assert r["rationale"][0].startswith("Excess embryos")
    assert "OHSS risk" in r["rationale"][1]
    assert "Endometrial issue" in r["rationale"][2]


def test_pgt_branch():
    r = assess({**_base(), "indication": "pgt"})
    assert r["procedure"] == "Embryo cryopreservation — for PGT biopsy and results"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert any("required step in the PGT process" in x for x in r["rationale"])


def test_defer_transfer_branch():
    r = assess({**_base(), "indication": "defer_transfer"})
    assert r["procedure"] == "Elective embryo cryopreservation — deferred transfer"
    assert r["cor"] == "IIa"
    assert r["loe"] == "B"


def test_donor_branch():
    r = assess({**_base(), "indication": "donor"})
    assert r["procedure"] == "Embryo cryopreservation — donor embryo banking"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert any("quarantine period" in x for x in r["rationale"])


def test_long_term_storage_warning():
    r = assess({**_base(), "storageYears": 12})
    assert any("Long-term storage (12 years)" in w for w in r["warnings"])


def test_storage_exactly_10_no_long_term_warning():
    r = assess({**_base(), "storageYears": 10})
    assert not any("Long-term storage" in w for w in r["warnings"])


def test_recommendation_constant():
    r = assess(_base())
    assert r["recommendation"] == "indicated"


def test_references_present():
    r = assess(_base())
    assert len(r["references"]) == 4
    assert r["references"][0].startswith("Practice Committees of ASRM and SART")
