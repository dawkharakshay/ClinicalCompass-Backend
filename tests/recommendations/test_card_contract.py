"""Every module's recommendation must conform to the uniform RecommendationCard.

Runs each registered engine and folds the output through the presentation layer,
asserting the envelope shape documented in docs/frontend/recommendation-card.md.
This guarantees the frontend can render any module with no per-module code.

Engines are exercised with an empty submission (defaults). A few engines raise on
genuinely empty input (they expect at least one field); those are listed in
``_NEEDS_INPUT`` and skipped here — their own module tests cover them with real
fixtures, and the mapper is shape-tested by the other ~100 modules regardless.
"""

import pytest

from app.recommendations import present_result
from app.recommendations.registry import REGISTRY

ENVELOPE = {
    "module", "title", "subtitle", "badges", "score", "alerts",
    "summary", "sections", "nextSteps", "evidence", "guidelineSource",
}
LIST_FIELDS = ["badges", "alerts", "sections", "nextSteps", "evidence"]
SECTION_TYPES = {"text", "list", "keyvalue"}
TONES = {"neutral", "info", "success", "warning", "danger"}

# Engines that need at least one real field to run (covered by their own tests).
_NEEDS_INPUT = {"all"}


@pytest.mark.parametrize("logic_key", sorted(REGISTRY))
def test_card_conforms_to_uniform_envelope(logic_key):
    if logic_key in _NEEDS_INPUT:
        pytest.skip(f"{logic_key} requires real input; covered by its module test")
    native = REGISTRY[logic_key]({})
    card = present_result(logic_key, native)

    assert ENVELOPE <= set(card), f"{logic_key}: missing {ENVELOPE - set(card)}"
    assert isinstance(card["title"], str) and card["title"], f"{logic_key}: empty title"
    for f in LIST_FIELDS:
        assert isinstance(card[f], list), f"{logic_key}: {f} must be a list"

    if card["score"] is not None:
        s = card["score"]
        assert isinstance(s.get("value"), (int, float))
        assert s.get("level") in {None, "high", "moderate", "low-moderate", "low"}

    for b in card["badges"]:
        assert b["tone"] in TONES, f"{logic_key}: bad badge tone {b['tone']}"
    for a in card["alerts"]:
        assert a["tone"] in TONES and isinstance(a["items"], list)
    for sec in card["sections"]:
        assert sec["type"] in SECTION_TYPES, f"{logic_key}: bad section type {sec['type']}"
        assert sec.get("label")


def test_coverage_is_essentially_complete():
    """Guard against silent regressions in how many engines produce a clean card."""
    runnable = [k for k in REGISTRY if k not in _NEEDS_INPUT]
    assert len(runnable) >= 99, f"expected ~100 runnable engines, got {len(runnable)}"
