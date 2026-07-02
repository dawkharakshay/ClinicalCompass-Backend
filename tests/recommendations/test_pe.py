"""Regression tests for the registered ``pe`` engine.

The engine dispatched for ``logicKey: "pe"`` must reproduce the old app's live
logic — ``classifyPE`` in ``peClassification.ts`` (ported to
``app.recommendations.shared.pe_classification``) — consuming the ``PatientData``
field names the PE form actually submits (``symptomatic``, ``systolicBP``,
``refractoryShock``, ``rvDysfunction``, ``tapse`` …).

Historically this engine ported ``peLogic.ts`` / ``evaluatePE`` instead — an
alternate implementation the old app never wired up, keyed on ``PEInput`` field
names (``presentation``, ``hemodynamicStatus``, ``rvStatus`` …). Because those
keys never matched the submission, every case fell through to defaults and
unstable patients were mis-categorised (a cardiac-arrest E2 patient came back
C2). These tests lock the fix in.
"""

from __future__ import annotations

from app.recommendations.registry import get_assessor, get_presenter
from app.recommendations.shared import pe_classification as pc


def assess(data: dict) -> dict:
    fn = get_assessor("pe")
    assert fn is not None, "no engine registered for logicKey 'pe'"
    return fn(data)


# ─── Dispatch wires to the live classifyPE port, not evaluatePE ───────────────
def test_registered_engine_is_classify_pe():
    fn = get_assessor("pe")
    assert fn.__module__ == "app.recommendations.modules.pe"
    # classifyPE output shape, not evaluatePE's (accAhaCategory/primaryRecommendation).
    r = assess({"symptomatic": True})
    assert "category" in r
    assert "accAhaCategory" not in r


def test_matches_classify_pe_exactly_for_real_numbers():
    sub = {
        "symptomatic": True,
        "refractoryShock": True,
        "cardiacArrest": True,
        "systolicBP": 70,
        "spO2": 88,
        "lactate": 5.0,
    }
    assert assess(sub) == pc.classify_pe(pc.patient_data(sub))


# ─── The actual bug: unstable patients must NOT collapse to Category C ────────
def test_cardiac_arrest_is_e2_not_c2():
    r = assess({"symptomatic": True, "cardiacArrest": True, "refractoryShock": True})
    assert r["category"] == "E2"
    assert r["riskLevel"] == "critical"


def test_persistent_hypotension_is_e1():
    r = assess({"symptomatic": True, "persistentHypotension": True, "systolicBP": 80})
    assert r["category"] == "E1"


def test_transient_hypotension_is_d1():
    r = assess({"symptomatic": True, "transientHypotension": True})
    assert r["category"] == "D1"


def test_normotensive_shock_is_d2():
    r = assess({"symptomatic": True, "normotensiveShock": True})
    assert r["category"] == "D2"


def test_incidental_is_category_a():
    r = assess({"symptomatic": False})
    assert r["category"] == "A"
    assert r["riskLevel"] == "minimal"


# ─── sPESI-driven Category C stratification (RV / biomarker) ──────────────────
def test_low_severity_symptomatic_is_b():
    # sPESI 0 (normal vitals, no comorbidity), non-subsegmental -> B2
    r = assess({"symptomatic": True, "systolicBP": 120, "heartRate": 80, "spO2": 98})
    assert r["category"] == "B2"


def test_elevated_severity_normal_rv_biomarker_is_c1():
    # sPESI >= 1 via SBP < 100, no RV dysfunction, no biomarker -> C1
    r = assess({"symptomatic": True, "systolicBP": 95})
    assert r["category"] == "C1"


def test_rv_or_biomarker_is_c2():
    r = assess({"symptomatic": True, "systolicBP": 95, "troponinElevated": True})
    assert r["category"] == "C2"


def test_rv_and_biomarker_is_c3():
    r = assess({"symptomatic": True, "systolicBP": 95,
                "rvDysfunction": True, "troponinElevated": True})
    assert r["category"] == "C3"


def test_tapse_below_threshold_counts_as_rv_dysfunction():
    r = assess({"symptomatic": True, "systolicBP": 95,
                "tapse": 1.4, "bnpElevated": True})
    assert r["category"] == "C3"  # abnormal RV (TAPSE<1.6) AND biomarker


# ─── Numeric coercion: stringy / blank inputs must not crash ──────────────────
def test_stringy_numbers_are_coerced():
    r = assess({"symptomatic": True, "systolicBP": "95", "age": "82", "cancer": True})
    assert r["category"] in {"C1", "C2", "C3"}


def test_blank_numbers_fall_back_to_defaults():
    r = assess({"symptomatic": True, "systolicBP": "", "spO2": "", "tapse": ""})
    assert "category" in r  # no exception


def test_blank_tapse_is_treated_as_null():
    r = assess({"symptomatic": True, "systolicBP": 95, "tapse": ""})
    # blank echo -> no TAPSE-driven RV dysfunction -> C1 (no biomarker either)
    assert r["category"] == "C1"


# ─── Card presentation ────────────────────────────────────────────────────────
def test_present_card_titles_with_category_and_risk():
    present = get_presenter("pe")
    assert present is not None
    card = present(assess({"symptomatic": True, "cardiacArrest": True,
                           "refractoryShock": True, "activeBleeding": True}))
    assert card["title"].startswith("Category E2")
    risk_badge = next(b for b in card["badges"] if b["label"] == "Risk")
    assert risk_badge["value"] == "Critical"
    assert risk_badge["tone"] == "danger"
    # active bleeding -> contraindication alert surfaced
    assert any(a["title"] == "Contraindications & Cautions" for a in card["alerts"])
    assert card["summary"]
