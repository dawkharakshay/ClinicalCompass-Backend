"""Tests for the JS-semantics helpers — the traps that differ from Python."""

import math

from app.recommendations import jslib


def test_parse_float():
    assert jslib.parse_float("12.5px") == 12.5
    assert jslib.parse_float("45") == 45.0
    assert jslib.parse_float(7) == 7.0
    assert math.isnan(jslib.parse_float(""))
    assert math.isnan(jslib.parse_float(None))
    assert math.isnan(jslib.parse_float("abc"))
    assert math.isnan(jslib.parse_float(True))  # booleans are not numbers to parseFloat


def test_num_falls_back_on_zero_and_nan():
    assert jslib.num("0", 44) == 44  # parseFloat("0") || 44
    assert jslib.num("", 44) == 44
    assert jslib.num(None, 44) == 44
    assert jslib.num("15", 44) == 15
    assert jslib.num("0", 0) == 0


def test_intnum():
    assert jslib.intnum("3", 0) == 3
    assert jslib.intnum("0", 0) == 0
    assert jslib.intnum("", 5) == 5
    assert jslib.intnum(None, 5) == 5
    assert jslib.intnum("2.9", 0) == 2


def test_truthy_matches_js():
    assert jslib.truthy("0") is True       # non-empty string -> truthy in JS
    assert jslib.truthy(0) is False
    assert jslib.truthy(0.0) is False
    assert jslib.truthy("") is False
    assert jslib.truthy(None) is False
    assert jslib.truthy([]) is True        # arrays are truthy in JS
    assert jslib.truthy({}) is True
    assert jslib.truthy(math.nan) is False


def test_coalesce_only_none():
    assert jslib.coalesce(0, 5) == 0       # ?? keeps 0
    assert jslib.coalesce("", "x") == ""   # ?? keeps ""
    assert jslib.coalesce(None, 5) == 5


def test_includes_none_safe():
    assert jslib.includes(["a", "b"], "a") is True
    assert jslib.includes(["a"], "z") is False
    assert jslib.includes(None, "a") is False


def test_js_round_half_up():
    assert jslib.js_round(0.5) == 1
    assert jslib.js_round(1.5) == 2
    assert jslib.js_round(-0.5) == 0       # JS Math.round(-0.5) === 0
    assert jslib.js_round(2.4) == 2


def test_pct_and_to_bool():
    assert jslib.pct(1, 4) == 25.0
    assert jslib.pct(1, 0) == 0.0
    assert jslib.to_bool("true") is True
    assert jslib.to_bool("false") is False
    assert jslib.to_bool(1) is True
    assert jslib.to_bool(0) is False


def test_minutes_between():
    assert jslib.js_minutes_between("2026-01-01T10:00:00", "2026-01-01T10:30:00") == 30.0
    assert jslib.js_minutes_between(None, "2026-01-01T10:30:00") == 0.0
    assert jslib.js_minutes_between("bad", "also-bad") == 0.0
