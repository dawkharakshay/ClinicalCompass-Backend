"""Uniform RecommendationCard presentation for the Rectal Cancer module.

Rectal has no module-specific ``present()``; it flows through the generic mapper
(app.recommendations.card.build_card). These tests pin the uniform envelope and
the score/evidence behaviour. The native engine shape is covered by
test_rectalcancer.py.
"""

from app.recommendations import present_result
from app.recommendations.modules.rectalcancer import EVIDENCE, assess

# Envelope keys guaranteed for every module's card.
_ENVELOPE = {
    "module", "title", "subtitle", "badges", "score", "alerts",
    "summary", "sections", "nextSteps", "evidence", "guidelineSource",
}


def _locally_advanced() -> dict:
    return {
        "tStage": "T3", "nStage": "N1", "mStage": "M0", "tumorLocation": "mid",
        "mrfStatus": "clear", "emviStatus": "negative",
        "responseAssessment": "not_assessed", "patientPreference": "no_preference",
        "surgicalFitness": "fit", "priorPelvicRT": False, "ibd": False, "msi_mmr": "MSS",
    }


def _card(over: dict | None = None) -> dict:
    data = _locally_advanced()
    if over:
        data.update(over)
    return present_result("rectalcancer", assess(data))


def test_card_has_uniform_envelope():
    card = _card()
    assert _ENVELOPE <= set(card)
    assert card["module"] == "rectalcancer"
    assert isinstance(card["badges"], list)
    assert isinstance(card["sections"], list)
    assert isinstance(card["nextSteps"], list)
    assert isinstance(card["evidence"], list)


def test_title_and_summary_from_engine():
    card = _card()
    assert card["title"] == "Standard Neoadjuvant CRT → TME"
    assert "intermediate-risk" in card["summary"]


def test_evidence_level_and_urgency_become_badges():
    badges = {b["label"]: b for b in _card()["badges"]}
    assert badges["Evidence"]["value"] == "Category 2A"
    assert badges["Urgency"]["value"] == "Routine"  # title-cased for display


def test_score_block_value_and_tier_track_the_form():
    base = _card()["score"]
    assert base["label"] == "Organ Preservation Score"
    assert base["value"] == 50 and base["max"] == 100
    assert base["level"] == "moderate"
    assert "Moderate" in base["note"]

    # cCR adds +25 -> 75, high tier.
    assert _card({"responseAssessment": "cCR"})["score"]["level"] == "high"
    # T4b + MRF involved + N2 drives it low.
    low = _card({"tStage": "T4b", "mrfStatus": "involved", "nStage": "N2"})["score"]
    assert low["value"] <= 30 and low["level"] == "low"


def test_evidence_attached_from_module_constant():
    card = _card()
    assert len(card["evidence"]) == len(EVIDENCE) == 6
    first = card["evidence"][0]
    assert {"title", "source", "description", "pmid"} <= set(first)
    assert first["pmid"] == "39151454"


def test_high_risk_warnings_surface_as_alerts():
    card = _card({"tStage": "T4b", "mrfStatus": "involved"})
    tones = {a["tone"] for a in card["alerts"]}
    assert card["alerts"]  # keyWarnings populated -> alerts present
    assert "warning" in tones
