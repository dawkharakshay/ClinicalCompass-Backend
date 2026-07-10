"""Generic engine-output → uniform RecommendationCard mapper.

Every ported engine returns a free-form ``dict`` whose keys vary by specialty.
This module folds *any* such dict into the single ``RecommendationCard`` envelope
the frontend renders generically (see ``docs/frontend/recommendation-card.md``):

    { module, title, subtitle, badges[], score|null, alerts[], summary,
      sections[], nextSteps[], evidence[], guidelineSource }

The mapping is fully data-driven (the config tables below) so adding a module
needs **no new code** here and **no frontend change** — common fields land in
the envelope, everything else becomes ordered ``sections``. A module may still
export its own ``present()`` to override this entirely.
"""

from __future__ import annotations

import re
from typing import Any

# ─── Field classification (data, not code) ────────────────────────────────────

# Title: first human-readable hit wins; codes are humanised as a last resort.
TITLE_KEYS = [
    "recommendationTitle", "strategyLabel", "primaryLabel", "title",
    "recommendation", "primaryRecommendation",
]
SUBTITLE_KEYS = ["subtitle", "strategySubtitle", "recommendationSubtitle"]
SUMMARY_KEYS = ["rationale", "clinicalRationale", "description", "summary", "reasoning"]
NEXT_STEPS_KEYS = ["nextSteps", "recommendedNextSteps", "next_steps"]
EVIDENCE_KEYS = ["evidence", "references", "citations"]
GUIDELINE_KEYS = ["guidelineSource", "guidelineSources", "guidelines", "guideline"]

# Badge key → display label, in display order.
BADGE_LABELS = {
    "severity": "Severity", "cor": "COR", "loe": "LOE",
    "evidenceLevel": "Evidence", "recommendationClass": "Class",
    "strength": "Strength", "certainty": "Certainty",
    "riskLevel": "Risk", "priority": "Priority", "urgency": "Urgency",
}
BADGE_ORDER = list(BADGE_LABELS)

# Alert key → (tone, heading).
ALERT_SPECS = {
    "urgentFlags": ("danger", "Urgent Flags"),
    "redFlags": ("danger", "Red Flags"),
    "contraindications": ("danger", "Contraindications"),
    "warnings": ("warning", "Warnings"),
    "keyWarnings": ("warning", "Key Warnings"),
    "cautions": ("warning", "Cautions"),
}

# Score key → config. ``levels`` (descending min → tier) is set ONLY where a
# higher value is genuinely "better" (green); omitted otherwise so the frontend
# shows a neutral value/max bar rather than a misleading colour.
_GOOD_LEVELS = [(70, "high"), (50, "moderate"), (30, "low-moderate"), (0, "low")]
SCORE_CONFIG: dict[str, dict] = {
    "organPreservationScore": {"label": "Organ Preservation Score", "max": 100,
                               "note": "organPreservationLabel", "levels": _GOOD_LEVELS},
    "candidacyScore": {"label": "Candidacy Score", "max": 100,
                       "note": "candidacyLabel", "levels": _GOOD_LEVELS},
    "score": {"label": "Score", "max": 100, "note": "scoreLabel", "levels": _GOOD_LEVELS},
    "tiRadsScore": {"label": "ACR TI-RADS", "max": None, "note": "tiRadsCategory"},
    "hasbledScore": {"label": "HAS-BLED", "max": 9, "note": None},
    "hestiaScore": {"label": "Hestia Criteria", "max": None, "note": None},
    "congestionScore": {"label": "Congestion Score", "max": None, "note": None},
}

# Acronyms to keep upper-cased when humanising keys.
_ACRONYMS = {
    "iop": "IOP", "tnt": "TNT", "crt": "CRT", "tme": "TME", "mri": "MRI",
    "dmt": "DMT", "cor": "COR", "loe": "LOE", "rads": "RADS", "glp1": "GLP-1",
    "esg": "ESG", "ww": "Watch-and-Wait", "bmi": "BMI", "ldl": "LDL",
    "msi": "MSI", "mmr": "MMR", "tnm": "TNM", "psa": "PSA", "ecog": "ECOG",
    "srs": "SRS", "wbrt": "WBRT", "pcv": "PCV", "rt": "RT", "iv": "IV",
}

_CODE_RE = re.compile(r"^[a-z][a-z0-9_]*$")  # snake/lower enum code, not display text


def _humanize(key: str) -> str:
    """``surgicalApproachLabel`` → ``Surgical Approach``; ``targetIOPRange`` →
    ``Target IOP Range``; ``ww_criteria`` → ``Watch-and-Wait Criteria``."""
    if key.endswith("Label"):
        key = key[: -len("Label")]
    s = key.replace("_", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)        # camelCase boundary
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)       # ACRONYMWord boundary
    out = []
    for w in s.split():
        lw = w.lower()
        if lw in _ACRONYMS:
            out.append(_ACRONYMS[lw])
        elif w.isupper():
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out) or key


def _is_code(value: str) -> bool:
    return bool(_CODE_RE.match(value))


def _truthy(v: Any) -> bool:
    return v not in (None, "", [], {}, ()) and not (isinstance(v, bool))


# ─── Piece builders ────────────────────────────────────────────────────────────


def _badge_tone(key: str, value: str) -> str:
    v = value.strip().lower()
    if key == "urgency":
        return {"emergent": "danger", "emergency": "danger", "urgent": "warning"}.get(v, "neutral")
    if key == "severity":
        if "severe" in v:
            return "danger"
        if "moderate" in v:
            return "warning"
        if "mild" in v:
            return "success"
        return "neutral"
    if key == "cor":
        return {"i": "success", "1": "success", "iia": "info", "2a": "info",
                "iib": "warning", "2b": "warning", "iii": "danger", "3": "danger"}.get(v, "info")
    if key == "strength":
        return "success" if "strong" in v else "info"
    if key in ("riskLevel",):
        if "high" in v:
            return "danger"
        if "moderate" in v or "intermediate" in v:
            return "warning"
        if "low" in v:
            return "success"
    return "info"


def _badges(native: dict) -> list[dict]:
    out = []
    for key in BADGE_ORDER:
        val = native.get(key)
        if isinstance(val, (str, int, float)) and str(val).strip():
            raw = str(val)
            display = raw.title() if raw.islower() else raw  # "routine" -> "Routine"
            out.append({"label": BADGE_LABELS[key], "value": display,
                        "tone": _badge_tone(key, raw)})
    return out


def _score(native: dict) -> dict | None:
    for key, cfg in SCORE_CONFIG.items():
        val = native.get(key)
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            continue
        score = {"label": cfg["label"], "value": val, "max": cfg.get("max")}
        note_key = cfg.get("note")
        if note_key and isinstance(native.get(note_key), str):
            score["note"] = native[note_key]
        levels = cfg.get("levels")
        if levels:
            score["level"] = next((lvl for lo, lvl in levels if val >= lo), levels[-1][1])
        else:
            score["level"] = None
        return score
    return None


def _alerts(native: dict) -> list[dict]:
    out = []
    for key, (tone, title) in ALERT_SPECS.items():
        items = native.get(key)
        if isinstance(items, list) and items:
            out.append({"tone": tone, "title": title,
                        "items": [str(x) for x in items]})
    return out


def _normalize_evidence(refs: Any) -> list[dict]:
    out = []
    for r in refs or []:
        if isinstance(r, dict):
            out.append({
                "title": r.get("title") or r.get("citation") or r.get("name"),
                "source": r.get("source") or r.get("authors"),
                "description": r.get("description"),
                "pmid": r.get("pmid"),
            })
        elif isinstance(r, str):
            out.append({"title": r, "source": None, "description": None, "pmid": None})
    return out


def _section_for(label: str, value: Any) -> dict | None:
    """Turn one leftover field into a section, or None to skip it."""
    if isinstance(value, str):
        return {"label": label, "type": "text", "content": value}
    if isinstance(value, (int, float)):
        return {"label": label, "type": "keyvalue", "items": [{"key": label, "value": str(value)}]}
    if isinstance(value, list):
        if all(isinstance(x, str) for x in value):
            return {"label": label, "type": "list", "items": list(value)}
        if all(isinstance(x, dict) for x in value):
            if all({"key", "value"} <= set(x) for x in value):
                return {"label": label, "type": "keyvalue",
                        "items": [{"key": str(x["key"]), "value": str(x["value"])} for x in value]}
            # generic list of dicts → readable lines
            return {"label": label, "type": "list",
                    "items": ["; ".join(f"{_humanize(k)}: {v}" for k, v in x.items()) for x in value]}
        return {"label": label, "type": "list", "items": [str(x) for x in value]}
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            if isinstance(v, (str, int, float)):
                items.append({"key": _humanize(k), "value": str(v)})
            elif isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                # list-valued sub-field (e.g. firstLineIntervention) — join like the
                # old frontend's ``.join(', ')`` rather than silently dropping it.
                items.append({"key": _humanize(k), "value": ", ".join(v)})
        if items:
            return {"label": label, "type": "keyvalue", "items": items}
    return None


# ─── Public entry point ─────────────────────────────────────────────────────────


def build_card(native: dict, logic_key: str | None = None,
               evidence: list | None = None) -> dict:
    """Map a native engine ``dict`` to the uniform RecommendationCard."""
    native = dict(native or {})
    consumed: set[str] = set()

    # title / subtitle
    title = None
    for k in TITLE_KEYS:
        v = native.get(k)
        if isinstance(v, str) and v.strip():
            title = _humanize(v) if _is_code(v) else v
            consumed.add(k)
            break
    subtitle = None
    for k in SUBTITLE_KEYS:
        v = native.get(k)
        if isinstance(v, str) and v.strip():
            subtitle, _ = v, consumed.add(k)
            break

    badges = _badges(native)
    consumed.update(k for k in BADGE_ORDER if native.get(k) not in (None, ""))

    score = _score(native)
    if score is not None:
        for k, cfg in SCORE_CONFIG.items():
            if native.get(k) is not None:
                consumed.add(k)
                if cfg.get("note"):
                    consumed.add(cfg["note"])

    alerts = _alerts(native)
    consumed.update(ALERT_SPECS)

    summary = None
    for k in SUMMARY_KEYS:
        v = native.get(k)
        if isinstance(v, str) and v.strip():
            summary, _ = v, consumed.add(k)
            break
        if isinstance(v, list):  # some engines return rationale as a list — keep as section
            break

    next_steps = []
    for k in NEXT_STEPS_KEYS:
        v = native.get(k)
        if isinstance(v, list):
            next_steps = [str(x) for x in v]
            consumed.add(k)
            break

    if evidence:
        ev = _normalize_evidence(evidence)
    else:
        ev = []
        for k in EVIDENCE_KEYS:
            if isinstance(native.get(k), list):
                ev = _normalize_evidence(native[k])
                break
    consumed.update(EVIDENCE_KEYS)

    guideline = None
    for k in GUIDELINE_KEYS:
        v = native.get(k)
        if isinstance(v, str) and v.strip():
            guideline = v
        elif isinstance(v, list) and v:
            guideline = "; ".join(str(x) for x in v)
        if guideline:
            consumed.add(k)
            break

    # everything left over → ordered sections
    sections = []
    for key, value in native.items():
        if key in consumed or not _truthy(value):
            continue
        if isinstance(value, str) and _is_code(value):
            continue  # machine code, not display text
        sec = _section_for(_humanize(key), value)
        if sec is not None:
            sec["id"] = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            sections.append(sec)

    return {
        "module": logic_key,
        "title": title or "Recommendation",
        "subtitle": subtitle,
        "badges": badges,
        "score": score,
        "alerts": alerts,
        "summary": summary,
        "sections": sections,
        "nextSteps": next_steps,
        "evidence": ev,
        "guidelineSource": guideline,
    }
