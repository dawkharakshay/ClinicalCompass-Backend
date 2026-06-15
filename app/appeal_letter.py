"""Render a personalized appeal letter from submission data + a DB-stored template.

The template is a JSON object (stored on ``Module.appeal_letter_template``) that
describes *how* to build the letter from a submission's answers, so the logic
lives in the database rather than in code. Shape::

    {
      "defaults":  { "<field>": "<fallback>" },      # used when an answer is missing
      "derived":   [ { "name", "rules": [{when, value}], "default" } ],
      "sections":  [ { "when": <cond>, "text": "..." } ],
      "section_separator": "\n\n",                    # optional, defaults to "\n"
      "template":  "free text with {{placeholders}} and {{sections}}"
    }

A condition (``when``) is either omitted (always true) or one of::

    { "field": "tStage", "op": "in", "value": ["T3", "T4"] }
    { "all": [ <cond>, ... ] }   { "any": [ <cond>, ... ] }   { "not": <cond> }

Supported ``op`` values: eq, ne, in, nin, gt, gte, lt, lte, exists, truthy.
"""

import re
from typing import Any

_PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _match(cond: dict | None, ctx: dict[str, Any]) -> bool:
    """Evaluate a condition against the current context."""
    if not cond:  # None or {} -> always true
        return True
    if "all" in cond:
        return all(_match(c, ctx) for c in cond["all"])
    if "any" in cond:
        return any(_match(c, ctx) for c in cond["any"])
    if "not" in cond:
        return not _match(cond["not"], ctx)

    field = cond.get("field")
    op = cond.get("op", "eq")
    expected = cond.get("value")
    actual = ctx.get(field)

    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in (expected or [])
    if op == "nin":
        return actual not in (expected or [])
    if op == "exists":
        return field in ctx and ctx[field] not in (None, "")
    if op == "truthy":
        return bool(actual)
    if op in ("gt", "gte", "lt", "lte"):
        try:
            a, e = float(actual), float(expected)
        except (TypeError, ValueError):
            return False
        return {
            "gt": a > e,
            "gte": a >= e,
            "lt": a < e,
            "lte": a <= e,
        }[op]
    return False


def _render_value(value: Any) -> str:
    """Stringify a context value; lists become bulleted lines."""
    if isinstance(value, (list, tuple)):
        return "\n".join(f"• {v}" for v in value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def render_appeal_letter(template: dict, data: dict) -> str:
    """Build a personalized appeal letter from ``data`` using ``template``."""
    defaults: dict[str, Any] = template.get("defaults") or {}

    # Context: defaults first, then the user's submitted answers override them.
    ctx: dict[str, Any] = {**defaults, **(data or {})}

    # Computed values: first matching rule wins, else the derived default.
    for spec in template.get("derived") or []:
        name = spec.get("name")
        if not name:
            continue
        value = spec.get("default")
        for rule in spec.get("rules") or []:
            if _match(rule.get("when"), ctx):
                value = rule.get("value")
                break
        ctx[name] = value

    # Conditional sections, joined into a single {{sections}} block.
    separator = template.get("section_separator", "\n")
    chosen = [
        s.get("text", "")
        for s in (template.get("sections") or [])
        if _match(s.get("when"), ctx)
    ]
    ctx["sections"] = separator.join(t for t in chosen if t)

    def _sub(m: "re.Match[str]") -> str:
        key = m.group(1).strip()
        if key in ctx and ctx[key] is not None:
            return _render_value(ctx[key])
        # Unknown/missing: fall back to a configured default, else leave as-is.
        return str(defaults[key]) if key in defaults else m.group(0)

    # Substitute repeatedly so placeholders produced by derived/section values
    # (one level of nesting) are themselves resolved. Stop when stable.
    text = template.get("template", "")
    for _ in range(5):
        new_text = _PLACEHOLDER.sub(_sub, text)
        if new_text == text:
            break
        text = new_text
    return text
