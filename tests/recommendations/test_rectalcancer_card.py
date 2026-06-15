"""Frontend-card presentation for the Rectal Cancer module.

The engine output (``assess``) is mapped by ``present`` into the normalized card
the frontend renders directly, with the static ``evidence`` list attached by the
presentation layer. The native engine shape is covered by test_rectalcancer.py.
"""

from app.recommendations import present_result
from app.recommendations.modules.rectalcancer import EVIDENCE, assess

# Card keys the frontend contract guarantees for this module.
_CARD_KEYS = {
    "title",
    "category",
    "description",
    "surgicalApproach",
    "organScore",
    "organScoreNote",
    "watchAndWait",
    "guidelineSource",
    "nextSteps",
    "evidence",
}


def _locally_advanced() -> dict:
    return {
        "tStage": "T3",
        "nStage": "N1",
        "mStage": "M0",
        "tumorLocation": "mid",
        "mrfStatus": "clear",
        "emviStatus": "negative",
        "responseAssessment": "not_assessed",
        "patientPreference": "no_preference",
        "surgicalFitness": "fit",
        "priorPelvicRT": False,
        "ibd": False,
        "msi_mmr": "MSS",
    }


def test_card_has_full_contract():
    card = present_result("rectalcancer", assess(_locally_advanced()))
    assert _CARD_KEYS <= set(card)


def test_card_maps_engine_fields():
    native = assess(_locally_advanced())
    card = present_result("rectalcancer", native)
    assert card["title"] == native["strategyLabel"]
    assert card["category"] == native["evidenceLevel"]
    assert card["description"] == native["rationale"]
    assert card["surgicalApproach"] == native["surgicalApproachLabel"]
    assert card["organScore"] == native["organPreservationScore"]
    assert card["organScoreNote"] == native["organPreservationLabel"]
    assert card["nextSteps"] == native["nextSteps"]


def test_watch_and_wait_rendered_as_display_string():
    card = present_result("rectalcancer", assess(_locally_advanced()))
    assert card["watchAndWait"] == "WATCH-AND-WAIT: NOT INDICATED"

    # cCR with organ-preservation preference -> W&W eligible.
    elig = _locally_advanced()
    elig["responseAssessment"] = "cCR"
    elig["patientPreference"] = "organ_preservation"
    card_elig = present_result("rectalcancer", assess(elig))
    assert card_elig["watchAndWait"] == "WATCH-AND-WAIT: ELIGIBLE"
    assert card_elig["watchAndWaitCriteria"]  # criteria carried through when eligible


def test_evidence_attached_verbatim():
    card = present_result("rectalcancer", assess(_locally_advanced()))
    assert card["evidence"] is EVIDENCE
    assert len(card["evidence"]) == 6
    assert {"title", "source", "description", "pmid"} <= set(card["evidence"][0])
    assert card["evidence"][0]["pmid"] == "39151454"


def test_unported_module_falls_back_to_native():
    """A module without present()/EVIDENCE returns the native engine output."""
    from app.recommendations.modules.migraine import assess as migraine_assess

    native = migraine_assess({"frequency": "chronic", "attacksPerMonth": 18})
    assert present_result("migraine", native) == native
