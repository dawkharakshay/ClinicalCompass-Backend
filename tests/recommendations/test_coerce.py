"""Tests for form-schema-driven submission coercion."""

from app.recommendations.coerce import coerce_submission

_FORM = {
    "steps": [
        {
            "fields": [
                {"name": "age", "type": "number"},
                {"name": "activeInfection", "type": "checkbox"},
                {"name": "comorbidities", "type": "multiselect"},
                {"name": "affectedSide", "type": "buttongroup"},
            ]
        }
    ]
}


def test_checkbox_to_bool():
    out = coerce_submission({"activeInfection": "true"}, _FORM)
    assert out["activeInfection"] is True
    assert coerce_submission({"activeInfection": "false"}, _FORM)["activeInfection"] is False


def test_multiselect_normalised_to_list():
    assert coerce_submission({"comorbidities": "diabetes"}, _FORM)["comorbidities"] == ["diabetes"]
    assert coerce_submission({"comorbidities": None}, _FORM)["comorbidities"] == []
    assert coerce_submission({"comorbidities": ["a", "b"]}, _FORM)["comorbidities"] == ["a", "b"]


def test_numbers_and_text_pass_through():
    out = coerce_submission({"age": "45", "affectedSide": "left"}, _FORM)
    assert out["age"] == "45"          # engine coerces numbers itself
    assert out["affectedSide"] == "left"


def test_unknown_keys_pass_through():
    out = coerce_submission({"mystery": "x"}, _FORM)
    assert out["mystery"] == "x"


def test_handles_missing_form():
    assert coerce_submission({"a": 1}, None) == {"a": 1}
    assert coerce_submission(None, _FORM) == {}
