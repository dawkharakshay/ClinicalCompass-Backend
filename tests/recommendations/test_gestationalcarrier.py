"""Gestational Carrier engine — fixtures derived from the inline evaluate()
function in GestationalCarrierCompass.tsx (no oracle *.test.ts exists)."""

from app.recommendations.modules.gestationalcarrier import assess


def _base() -> dict:
    return {
        "congenitalAbsenceUterus": False,
        "surgicalAbsenceUterus": False,
        "ashermansSyndrome": False,
        "uterineMalformation": False,
        "recurrentImplantationFailure": False,
        "medicalContraindication": False,
        "medicalContraindicationDetail": "",
        "recurrentPregnancyLoss": False,
        "priorIVFFailure": False,
        "singleIntendedParent": False,
        "sameGenderCouple": False,
        "carrierIdentified": False,
        "carrierScreeningComplete": False,
        "legalAgreementComplete": False,
    }


def test_medical_indication_congenital():
    r = assess({**_base(), "congenitalAbsenceUterus": True})
    assert r["recommendation"] == "indicated"
    assert r["procedure"] == "Gestational carrier (surrogacy) — medical indication"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert any("MRKH syndrome" in x for x in r["rationale"])
    # carrier not identified + legal not complete -> 1 medical warning + 2 screening warnings
    assert len(r["warnings"]) == 3


def test_medical_contraindication_uses_detail_when_present():
    r = assess(
        {
            **_base(),
            "medicalContraindication": True,
            "medicalContraindicationDetail": "pulmonary hypertension",
            "carrierIdentified": True,
            "legalAgreementComplete": True,
        }
    )
    assert r["recommendation"] == "indicated"
    assert any("pulmonary hypertension" in x for x in r["rationale"])
    # only the medical-necessity warning; carrier + legal complete
    assert len(r["warnings"]) == 1


def test_medical_contraindication_falls_back_when_detail_blank():
    r = assess(
        {
            **_base(),
            "medicalContraindication": True,
            "medicalContraindicationDetail": "",
        }
    )
    assert any(
        "documented medical condition" in x for x in r["rationale"]
    )


def test_relative_indication_implantation_failure():
    r = assess({**_base(), "recurrentImplantationFailure": True})
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIb"
    assert r["loe"] == "C"
    assert r["procedure"] == "Gestational carrier — relative indication (shared decision-making)"


def test_relative_indication_pregnancy_loss():
    r = assess({**_base(), "recurrentPregnancyLoss": True})
    assert r["recommendation"] == "consider"
    assert r["cor"] == "IIb"


def test_medical_indication_overrides_relative():
    # both medical and relative flags -> medical branch wins
    r = assess(
        {**_base(), "ashermansSyndrome": True, "recurrentImplantationFailure": True}
    )
    assert r["recommendation"] == "indicated"
    assert r["cor"] == "I"
    # relative-indication rationale must NOT be present
    assert not any("Relative indication" in x for x in r["rationale"])


def test_not_indicated_default():
    r = assess(_base())
    assert r["recommendation"] == "not_indicated"
    assert r["procedure"] == "Gestational carrier — no medical indication identified"
    assert r["cor"] == "I"
    assert r["loe"] == "B"
    assert r["rationale"] == []
    # social warning + carrier + legal warnings
    assert len(r["warnings"]) == 3
    assert any("Social/elective" in x for x in r["warnings"])


def test_carrier_and_legal_complete_suppress_warnings():
    r = assess(
        {
            **_base(),
            "congenitalAbsenceUterus": True,
            "carrierIdentified": True,
            "legalAgreementComplete": True,
        }
    )
    assert len(r["warnings"]) == 1
    assert not any("not yet identified" in x for x in r["warnings"])
    assert not any("Legal agreement" in x for x in r["warnings"])


def test_references_always_present():
    r = assess(_base())
    assert len(r["references"]) == 3
    assert all("ASRM" in x or "ACOG" in x for x in r["references"])
