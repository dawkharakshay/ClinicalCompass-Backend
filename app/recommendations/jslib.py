"""JavaScript-semantics helpers for the ported recommendation engines.

The legacy logic was TypeScript; porting it 1:1 means reproducing a handful of
JS behaviours that differ from Python. Centralise them here so every module
port shares the same primitives and the traps are fixed (and tested) once.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

_NUM_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def parse_float(x: Any) -> float:
    """JS ``parseFloat``: leading numeric prefix of a string, else NaN.

    ``parseFloat("12.5px") == 12.5``, ``parseFloat("") is NaN``,
    ``parseFloat(None) is NaN``. Booleans are NOT numbers to parseFloat (NaN),
    but real ints/floats pass through.
    """
    if x is None or isinstance(x, bool):
        return math.nan
    if isinstance(x, (int, float)):
        return float(x)
    m = _NUM_RE.match(str(x).strip())
    return float(m.group(0)) if m else math.nan


def num(x: Any, default: float = 0.0) -> float:
    """JS ``parseFloat(x) || default`` — note 0 AND NaN both fall back.

    This mirrors the dominant idiom in the legacy logic (e.g.
    ``parseFloat(input.bmi) || 0``). Use :func:`parse_float` when a literal 0
    must be preserved.
    """
    v = parse_float(x)
    return float(default) if (math.isnan(v) or v == 0) else v


def intnum(x: Any, default: int = 0) -> int:
    """JS ``parseInt(x) || default`` (base-10, 0/NaN -> default)."""
    if isinstance(x, bool):
        return default
    if isinstance(x, (int, float)):
        return int(x) or default
    m = re.match(r"[+-]?\d+", str(x).strip()) if x is not None else None
    return (int(m.group(0)) or default) if m else default


def truthy(x: Any) -> bool:
    """JS truthiness. Falsy: False, 0, 0.0, NaN, "", None. Everything else
    (including "0", "false", [], {}) is truthy — note [] and {} differ from Python.
    """
    if x is None:
        return False
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x != 0 and not (isinstance(x, float) and math.isnan(x))
    if isinstance(x, str):
        return x != ""
    return True  # objects and arrays are truthy in JS


def coalesce(x: Any, default: Any) -> Any:
    """JS ``??`` — fall back only on null/undefined (None), NOT on 0/""/False."""
    return default if x is None else x


def includes(seq: Any, value: Any) -> bool:
    """JS ``Array.prototype.includes`` — None-safe membership."""
    if not seq:
        return False
    try:
        return value in seq
    except TypeError:
        return False


def js_round(x: float) -> int:
    """JS ``Math.round`` — round half toward +infinity (not Python's banker's)."""
    if math.isnan(x):
        return 0
    return math.floor(x + 0.5)


def pct(numerator: float, denominator: float) -> float:
    """Percentage with divide-by-zero guard (0 when denominator is 0)."""
    return (numerator / denominator) * 100 if denominator else 0.0


def to_bool(x: Any) -> bool:
    """Coerce a submitted value to a boolean (handles real bools and the
    string forms ``"true"/"false"/"1"/"0"/"yes"/"no"`` and numbers)."""
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x != 0
    if isinstance(x, str):
        return x.strip().lower() in {"true", "1", "yes", "y", "on"}
    return bool(x)


def js_minutes_between(start: Any, end: Any) -> float:
    """Minutes between two ISO datetime strings (``(end - start) / 60000`` in JS).

    Returns 0.0 when either value is missing or unparseable.
    """
    def _parse(v: Any) -> datetime | None:
        if not v:
            return None
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError:
            return None

    a, b = _parse(start), _parse(end)
    if a is None or b is None:
        return 0.0
    return (b - a).total_seconds() / 60.0
