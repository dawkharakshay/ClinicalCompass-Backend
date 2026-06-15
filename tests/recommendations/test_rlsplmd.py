"""RLS / PLMD engine — fixtures derived from the inline evaluate() branches in
old_static_code/client/src/pages/RLSPLMDCompass.tsx."""

from app.recommendations.modules.rlsplmd import assess


def _base() -> dict:
    # All boolean defaults False, all numeric fields empty strings — matches
    # the page's defaultInputs (severity "unknown").
    return {
        "irlss_score": "",
        "plmi": "",
        "plm_diagnosis": False,
        "rls_diagnosis": False,
        "duration_years": "",
        "ferritin": "",
        "transferrin_sat": "",
        "iron_infusion_tried": False,
        "prior_gabapentin": False,
        "prior_pregabalin": False,
        "prior_gabapentin_enacarbil": False,
        "prior_pramipexole": False,
        "prior_ropinirole": False,
        "augmentation": False,
        "renal_impairment": False,
        "egfr": "",
        "pregnancy": False,
        "comorbid_depression": False,
        "comorbid_anxiety": False,
        "severity": "unknown",
    }


def test_empty_defaults():
    r = assess(_base())
    # No IRLSS -> falls back to inputs.severity ("unknown")
    assert r["severity"] == "unknown"
    # Empty ferritin -> NaN -> not iron deficient
    assert r["ironDeficient"] is False
    # All three alpha-2-delta ligands recommended (none tried)
    assert sum("STRONGLY RECOMMENDED" in x for x in r["recommendations"]) == 3
    # No DA tried -> generic CPG-update note
    assert any("Prefer alpha-2-delta ligands as first-line" in n for n in r["notes"])
    assert r["contraindications"] == []
    assert r["authRequired"] is True
    # rls_diagnosis False -> moderate
    assert r["appealStrength"] == "moderate"
    # No IRLSS, no PLMI, not iron deficient, no augmentation -> no key findings
    assert r["keyFindings"] == []


def test_severity_bands():
    assert assess({**_base(), "irlss_score": "31"})["severity"] == "severe"
    assert assess({**_base(), "irlss_score": "21"})["severity"] == "moderate-severe"
    assert assess({**_base(), "irlss_score": "11"})["severity"] == "moderate"
    assert assess({**_base(), "irlss_score": "1"})["severity"] == "mild"
    # 0 falls through to inputs.severity
    assert assess({**_base(), "irlss_score": "0", "severity": "mild"})["severity"] == "mild"


def test_iron_deficient_low_ferritin_iv_iron():
    r = assess({**_base(), "ferritin": "50"})
    assert r["ironDeficient"] is True
    assert any("IV Ferric Carboxymaltose (Injectafer)" in x for x in r["recommendations"])
    assert any("Target serum ferritin" in x for x in r["recommendations"])
    assert any("Iron deficiency: Ferritin 50 ng/mL" in f for f in r["keyFindings"])


def test_iron_deficient_transferrin_branch():
    # ferritin 90 (>=75 so first clause false) but <100 with TSAT <20 -> deficient
    r = assess({**_base(), "ferritin": "90", "transferrin_sat": "15"})
    assert r["ironDeficient"] is True
    # ferritin 90 with TSAT 25 -> NOT deficient (both clauses false)
    r2 = assess({**_base(), "ferritin": "90", "transferrin_sat": "25"})
    assert r2["ironDeficient"] is False


def test_iron_infusion_already_tried_note():
    r = assess({**_base(), "ferritin": "50", "iron_infusion_tried": True})
    assert r["ironDeficient"] is True
    assert not any("IV Ferric Carboxymaltose" in x for x in r["recommendations"])
    assert any("IV iron infusion previously attempted" in n for n in r["notes"])


def test_da_with_augmentation_contraindication():
    r = assess({**_base(), "prior_pramipexole": True, "augmentation": True})
    assert any("AUGMENTATION DOCUMENTED" in c for c in r["contraindications"])
    assert any("Augmentation documented" in f for f in r["keyFindings"])


def test_da_tried_no_augmentation_note():
    r = assess({**_base(), "prior_ropinirole": True})
    assert r["contraindications"] == []
    assert any("Monitor for augmentation using IRLSS trends" in n for n in r["notes"])


def test_renal_impairment_egfr():
    r = assess({**_base(), "egfr": "45"})
    assert any("Renal impairment (eGFR: 45)" in n for n in r["notes"])
    # renal_impairment flag with empty egfr -> "reduced"
    r2 = assess({**_base(), "renal_impairment": True})
    assert any("Renal impairment (eGFR: reduced)" in n for n in r2["notes"])


def test_pregnancy():
    r = assess({**_base(), "pregnancy": True})
    assert any("Pregnancy: Avoid pharmacotherapy in first trimester" in x for x in r["recommendations"])
    assert any("consult MFM/obstetrics" in n for n in r["notes"])


def test_plmd_branch():
    r = assess({**_base(), "plm_diagnosis": True, "plmi": "20"})
    assert any("PLMD (PLMI: 20 events/hour)" in x for x in r["recommendations"])
    assert any("PLMI: 20 events/hour — PLMD diagnosis criteria met" in f for f in r["keyFindings"])
    # plmi below 15 -> no PLMD recommendation, key finding without "met" suffix
    r2 = assess({**_base(), "plm_diagnosis": True, "plmi": "10"})
    assert not any("PLMD (PLMI" in x for x in r2["recommendations"])
    assert any("PLMI: 10 events/hour" in f and "criteria met" not in f for f in r2["keyFindings"])


def test_appeal_strength_strong():
    r = assess({**_base(), "rls_diagnosis": True, "irlss_score": "15"})
    assert r["appealStrength"] == "strong"
    # rls_diagnosis True but irlss <11 -> moderate
    r2 = assess({**_base(), "rls_diagnosis": True, "irlss_score": "5"})
    assert r2["appealStrength"] == "moderate"


def test_key_finding_irlss():
    r = assess({**_base(), "irlss_score": "35"})
    assert any("IRLSS Score: 35/40 — severe RLS" in f for f in r["keyFindings"])
