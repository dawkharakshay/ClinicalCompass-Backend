"""Maps a form's ``logicKey`` to its ported assessment function.

Dispatch key is ``Module.form["logicKey"]`` (present on every seeded form).
Registration is **auto-discovered**: every module in ``app.recommendations.modules``
that declares a ``LOGIC_KEY`` string and an ``assess(data) -> dict`` callable is
registered automatically. Dropping a new ``modules/<x>.py`` is therefore all it
takes to add an engine — no edit to this file (keeps parallel porting conflict-free).

A ``logicKey`` with no registered engine -> the endpoint returns 404 (not yet
ported, or a coming-soon stub).
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

from app.recommendations import modules as _modpkg

# Homoglyph normalisation: a couple of legacy logicKeys carry Cyrillic look-
# alikes (e.g. "atherecтomy"). Normalise before lookup so dispatch matches
# the clean Latin registry key.
_HOMOGLYPHS = {"т": "t", "о": "o", "н": "n", "а": "a",
               "е": "e", "с": "c", "р": "p", "х": "x"}


def _normalize(key: str) -> str:
    return "".join(_HOMOGLYPHS.get(ch, ch) for ch in key)


def _discover() -> tuple[
    dict[str, Callable[[dict], dict]],
    dict[str, Callable[[dict], dict]],
    dict[str, list],
]:
    """Scan ``modules/`` once and collect, per normalised LOGIC_KEY:

    - ``assess``   -> the recommendation engine (required to register a key)
    - ``present``  -> optional native-result -> frontend-card mapper
    - ``EVIDENCE`` -> optional static reference list attached to the card

    ``present``/``EVIDENCE`` are additive: a module without them still works
    (the endpoint falls back to the native engine output), so the card rollout
    can proceed module-by-module without breaking unported ones.
    """
    assessors: dict[str, Callable[[dict], dict]] = {}
    presenters: dict[str, Callable[[dict], dict]] = {}
    evidence: dict[str, list] = {}
    for _, name, _ in pkgutil.iter_modules(_modpkg.__path__):
        try:
            mod = importlib.import_module(f"app.recommendations.modules.{name}")
        except Exception as exc:  # noqa: BLE001 - one bad module must not break the rest
            import logging
            logging.getLogger(__name__).warning("recommendation module %s failed to import: %s", name, exc)
            continue
        key = getattr(mod, "LOGIC_KEY", None)
        fn = getattr(mod, "assess", None)
        if not (isinstance(key, str) and callable(fn)):
            continue
        nkey = _normalize(key)
        assessors[nkey] = fn
        presenter = getattr(mod, "present", None)
        if callable(presenter):
            presenters[nkey] = presenter
        ev = getattr(mod, "EVIDENCE", None)
        if isinstance(ev, list):
            evidence[nkey] = ev
    return assessors, presenters, evidence


REGISTRY, PRESENTERS, EVIDENCE = _discover()


def get_assessor(logic_key: str | None) -> Callable[[dict], dict] | None:
    """Return the assess() callable for a form's logicKey, or None if unported."""
    if not logic_key:
        return None
    return REGISTRY.get(_normalize(logic_key))


def get_presenter(logic_key: str | None) -> Callable[[dict], dict] | None:
    """Return the present() card-mapper for a logicKey, or None if not defined."""
    if not logic_key:
        return None
    return PRESENTERS.get(_normalize(logic_key))


def get_evidence(logic_key: str | None) -> list | None:
    """Return the static EVIDENCE list for a logicKey, or None if not defined."""
    if not logic_key:
        return None
    return EVIDENCE.get(_normalize(logic_key))


def present_result(logic_key: str | None, native: dict) -> dict:
    """Build the uniform RecommendationCard from an engine's native output.

    A module may export its own ``present(native) -> dict`` to fully control its
    card; otherwise the generic mapper (:func:`app.recommendations.card.build_card`)
    folds the native output into the uniform envelope — so every module yields the
    same shape with no per-module code. The module's static ``EVIDENCE`` list, when
    declared, is attached as the card's references.
    """
    from app.recommendations.card import build_card

    evidence = get_evidence(logic_key)
    presenter = get_presenter(logic_key)
    if presenter:
        card = presenter(native)
        if evidence is not None and not card.get("evidence"):
            card["evidence"] = evidence
        return card
    return build_card(native, logic_key=logic_key, evidence=evidence)
