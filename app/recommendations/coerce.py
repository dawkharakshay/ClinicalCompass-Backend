"""Coerce a verbatim submission dict into the typed shape the ported engines
expect, driven by the module's own form-field ``type``s.

The legacy UI handed engines real booleans for checkboxes and ``string[]`` for
multiselects, but plain strings for everything numeric/textual (the engines
then ``parseFloat``/``parseInt`` internally). We reproduce exactly that: only
``checkbox`` -> bool and ``multiselect`` -> list are normalised; numbers and
text are passed through as-is for each engine's own coercion (see jslib.num).
"""

from __future__ import annotations

from typing import Any

from app.recommendations.jslib import to_bool


def _field_types(form: dict | None) -> dict[str, str]:
    """Map field ``name`` -> field ``type`` across all steps of a form."""
    types: dict[str, str] = {}
    for step in (form or {}).get("steps", []) or []:
        for field in step.get("fields", []) or []:
            name = field.get("name")
            if name:
                types[name] = field.get("type", "")
    return types


def coerce_submission(data: dict | None, form: dict | None) -> dict[str, Any]:
    """Return a shallow copy of ``data`` with checkbox/multiselect values
    normalised per the form schema. Unknown keys pass through untouched."""
    data = dict(data or {})
    types = _field_types(form)
    for name, value in list(data.items()):
        ftype = types.get(name)
        if ftype == "checkbox":
            data[name] = to_bool(value)
        elif ftype == "multiselect":
            if value is None:
                data[name] = []
            elif isinstance(value, list):
                pass
            else:
                data[name] = [value]
        # number/slider/select/buttongroup/text and unknowns: leave as-is;
        # the engine coerces numbers itself (jslib.num/intnum).
    return data
