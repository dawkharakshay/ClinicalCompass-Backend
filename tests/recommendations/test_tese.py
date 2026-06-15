"""TESE / Micro-TESE engine — fixtures derived directly from the inline
evaluate() branches in TESECompass.tsx."""

from app.recommendations.modules.tese import assess


def _base() -> dict:
    return {
        "azoospermiaType": "non_obstructive",
        "fshLevel": 0,
        "lhLevel": 0,
        "testosteroneLevel": 0,
        "inhibinB": 0,
        "testisVolume": "reduced",
        "karyotype": "not_done",
        "cftrMutation": False,
        "priorTESE": False,
        "priorTESEResult": "not_done",
        "histologyAvailable": False,
        "histologyPattern": "not_done",
        "partnerAge": 0,
        "oncologyPatient": False,
    }


def test_obstructive_is_class_i_loe_a():
    r = assess({**_base(), "azoospermiaType": "obstructive"})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Conventional TESE or PESA/MESA (obstructive azoospermia)"
    assert r["cor"] == "I"
    assert r["loe"] == "A"
    assert r["successRate"] == "~90–100% sperm retrieval"
    assert any("Obstructive azoospermia" in x for x in r["rationale"])


def test_unknown_type_not_indicated():
    r = assess({**_base(), "azoospermiaType": "unknown"})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == ""
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert r["rationale"] == []
    assert r["warnings"] == []


def test_noa_default_estimated_success():
    r = assess({**_base()})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Microdissection TESE (micro-TESE) — preferred for NOA"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert r["successRate"] == "~40–60% sperm retrieval (estimated)"


def test_noa_hypospermatogenesis():
    r = assess({**_base(), "histologyPattern": "hypospermatogenesis"})
    assert r["successRate"] == "~70–80% sperm retrieval"


def test_noa_maturation_arrest():
    r = assess({**_base(), "histologyPattern": "maturation_arrest"})
    assert r["successRate"] == "~30–50% sperm retrieval"


def test_noa_sertoli_only():
    r = assess({**_base(), "histologyPattern": "sertoli_only"})
    assert r["successRate"] == "~15–30% sperm retrieval"


def test_azfa_deletion_contraindicated():
    r = assess({**_base(), "karyotype": "y_deletion_azfa"})
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "TESE NOT recommended — AZFa or AZFb deletion"
    assert r["cor"] == "III"
    assert r["loe"] == "A"
    assert any("virtually impossible" in w for w in r["warnings"])


def test_azfb_deletion_contraindicated():
    r = assess({**_base(), "karyotype": "y_deletion_azfb"})
    assert r["recommendation"] == "not_indicated"
    assert r["cor"] == "III"
    assert r["loe"] == "A"


def test_azfc_deletion_warning_only():
    r = assess({**_base(), "karyotype": "y_deletion_azfc"})
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "I"
    assert any("AZFc deletion" in w for w in r["warnings"])


def test_klinefelter_overrides_success_rate():
    r = assess({**_base(), "histologyPattern": "sertoli_only", "karyotype": "klinefelter"})
    # Klinefelter branch overwrites the histology-derived success rate.
    assert r["successRate"] == "~40–60% sperm retrieval"
    assert any("Klinefelter" in w for w in r["warnings"])
    assert any("Klinefelter syndrome: micro-TESE is the preferred" in x for x in r["rationale"])


def test_hormonal_and_partner_warnings():
    r = assess({**_base(), "fshLevel": 25, "inhibinB": 30, "partnerAge": 39,
                "oncologyPatient": True})
    w = " ".join(r["warnings"])
    assert "Markedly elevated FSH (25 mIU/mL)" in w
    assert "Low inhibin B (30 pg/mL)" in w
    assert "Partner age 39" in w
    assert "Oncology patient" in w
    assert any("ASCO guidelines" in x for x in r["rationale"])


def test_inhibin_zero_does_not_warn():
    # inhibinB == 0 must NOT trigger the low-inhibin warning (< 40 && > 0).
    r = assess({**_base(), "inhibinB": 0})
    assert not any("Low inhibin B" in w for w in r["warnings"])


def test_prior_tese_no_sperm_warning():
    r = assess({**_base(), "priorTESE": True, "priorTESEResult": "no_sperm"})
    assert any("Prior TESE with no sperm found" in w for w in r["warnings"])


def test_prior_tese_sperm_found_no_warning():
    r = assess({**_base(), "priorTESE": True, "priorTESEResult": "sperm_found"})
    assert not any("Prior TESE" in w for w in r["warnings"])
