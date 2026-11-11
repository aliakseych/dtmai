from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.exam_info.domain.models import (
    CertRule,
    Claim,
    ExamEvent,
    ExamProfile,
    ExamProfileInvalid,
    FaqItem,
    Section,
    cefr_ordinal,
    evaluate_exemptions,
    localize,
    projected_score,
    total_points,
    validate_profile,
    validate_rule,
)
from app.shared.errors import ValidationFailed

T = {"en": "x", "ru": "x", "uz-Latn": "x", "uz-Cyrl": "x"}
D = Decimal


def sec(role: str, slot: int, *, group: str | None = None, exemptible: bool = True) -> Section:
    if role == "iq":
        return Section(uuid4(), "iq", 0, T, None, None, None, 20, D("1.1"), D("22"), False)
    return Section(uuid4(), role, slot, T, None, None, group, 20, D("3.1"), D("62"), exemptible)


def rule(section: Section, cert: str, min_value: str | None, **kw: object) -> CertRule:
    return CertRule(
        uuid4(),
        section.id,
        cert,
        min_value=None if min_value is None else D(min_value),
        **kw,  # type: ignore[arg-type]
    )


def profile(*sections: Section) -> ExamProfile:
    return ExamProfile(uuid4(), "p", "academic_lyceum", T, 2027, D("146"), sections=sections)


def test_score_math_is_146() -> None:
    iq, a, b = sec("iq", 0), sec("subject", 1), sec("subject", 2)
    assert total_points([iq, a, b]) == D("146")
    validate_profile(profile(iq, a, b))


def test_profile_rejects_wrong_total() -> None:
    with pytest.raises(ExamProfileInvalid):
        validate_profile(profile(sec("iq", 0), sec("subject", 1)))


def test_section_points_must_match_question_math() -> None:
    with pytest.raises(ExamProfileInvalid):
        Section(uuid4(), "subject", 1, T, None, None, None, 20, D("3.1"), D("60"), True)


def test_iq_section_cannot_be_exemptible() -> None:
    with pytest.raises(ExamProfileInvalid):
        Section(uuid4(), "iq", 0, T, None, None, None, 20, D("1.1"), D("22"), True)


def test_iq_must_be_slot_zero() -> None:
    with pytest.raises(ExamProfileInvalid):
        Section(uuid4(), "subject", 0, T, None, None, None, 20, D("3.1"), D("62"), True)


def test_creative_section_is_not_in_app() -> None:
    creative = Section(uuid4(), "creative", 2, T, max_points=D("62"), exemptible=False)
    p = profile(sec("iq", 0), sec("subject", 1), creative)
    validate_profile(p)
    assert creative not in p.planned_sections
    assert total_points(p.planned_sections) == D("84")


def test_iq_never_exempt_even_with_rule_and_claim() -> None:
    iq = sec("iq", 0)
    exempt = evaluate_exemptions(
        (iq,), (rule(iq, "national", "1"),), [Claim(iq.id, "national", D("100"))]
    )
    assert exempt == []


def test_language_certificate_gives_full_points() -> None:
    iq, math, lang = sec("iq", 0), sec("subject", 1), sec("subject", 2, group="foreign_language")
    r = rule(lang, "ielts", "5.0")
    out = evaluate_exemptions((iq, math, lang), (r,), [Claim(lang.id, "ielts", D("5.5"))])
    assert [(e.section_id, e.points, e.rule_id) for e in out] == [(lang.id, D("62"), r.id)]


def test_claim_below_minimum_is_ignored() -> None:
    lang = sec("subject", 1, group="foreign_language")
    out = evaluate_exemptions(
        (lang,), (rule(lang, "ielts", "5.0"),), [Claim(lang.id, "ielts", D("4.5"))]
    )
    assert out == []


def test_language_certificate_not_valid_for_non_language_section() -> None:
    math = sec("subject", 1)
    out = evaluate_exemptions(
        (math,), (rule(math, "ielts", "5.0"),), [Claim(math.id, "ielts", D("9"))]
    )
    assert out == []


def test_national_certificate_applies_to_any_subject_when_enabled() -> None:
    math = sec("subject", 1)
    r = rule(math, "national", "70")
    assert evaluate_exemptions((math,), (r,), [Claim(math.id, "national", D("70"))])[0].points == D(
        "62"
    )


def test_inactive_or_unset_minimum_rules_are_ignored() -> None:
    math = sec("subject", 1)
    claims = [Claim(math.id, "national", D("100"))]
    assert evaluate_exemptions((math,), (rule(math, "national", "70", active=False),), claims) == []
    assert evaluate_exemptions((math,), (rule(math, "national", None, active=False),), claims) == []


def test_best_fraction_wins() -> None:
    lang = sec("subject", 1, group="foreign_language")
    low = rule(lang, "cefr", "3", awarded_fraction=D("0.5"))
    high = rule(lang, "ielts", "5.0")
    out = evaluate_exemptions(
        (lang,), (low, high), [Claim(lang.id, "cefr", D("4")), Claim(lang.id, "ielts", D("6"))]
    )
    assert len(out) == 1 and out[0].rule_id == high.id


def test_rule_language_must_match_claim() -> None:
    lang = sec("subject", 1, group="foreign_language")
    en, de = uuid4(), uuid4()
    r = rule(lang, "cefr", "3", language_subject_id=en)
    assert evaluate_exemptions((lang,), (r,), [Claim(lang.id, "cefr", D("3"), de)]) == []
    assert len(evaluate_exemptions((lang,), (r,), [Claim(lang.id, "cefr", D("3"), en)])) == 1


def test_projected_score_uses_exemptions_and_caps() -> None:
    iq, math, lang = sec("iq", 0), sec("subject", 1), sec("subject", 2, group="foreign_language")
    ex = evaluate_exemptions(
        (lang,), (rule(lang, "ielts", "5.0"),), [Claim(lang.id, "ielts", D("6"))]
    )
    score = projected_score((iq, math, lang), ex, {iq.id: D("20"), math.id: D("70")})
    assert score == D("20") + D("62") + D("62")


def test_cefr_ordinal() -> None:
    assert cefr_ordinal("b1") == 3
    assert cefr_ordinal("C2") == 6
    with pytest.raises(ValidationFailed):
        cefr_ordinal("D1")


def test_validate_rule_guards() -> None:
    iq, math, lang = sec("iq", 0), sec("subject", 1), sec("subject", 2, group="foreign_language")
    with pytest.raises(ValidationFailed) as e:
        validate_rule(iq, "national", True, D("1"), D(1))
    assert e.value.code == "section_not_exemptible"
    with pytest.raises(ValidationFailed) as e:
        validate_rule(math, "ielts", True, D("5"), D(1))
    assert e.value.code == "cert_type_not_allowed"
    with pytest.raises(ValidationFailed) as e:
        validate_rule(lang, "ielts", True, None, D(1))
    assert e.value.code == "min_value_required"
    with pytest.raises(ValidationFailed):
        validate_rule(lang, "ielts", True, D("5"), D("1.5"))
    validate_rule(math, "national", False, None, D(1))


def test_event_range_and_kind() -> None:
    from datetime import date

    with pytest.raises(ValidationFailed):
        ExamEvent(uuid4(), 2027, "test", date(2027, 7, 26), T, date(2027, 7, 25))
    with pytest.raises(ValidationFailed):
        ExamEvent(uuid4(), 2027, "party", date(2027, 7, 26), T)


def test_faq_requires_all_locales() -> None:
    with pytest.raises(ValidationFailed) as e:
        FaqItem(uuid4(), "k", "c", {"en": "q"}, T)
    assert e.value.code == "locales_missing"


def test_localize_falls_back() -> None:
    assert localize({"en": "hi", "ru": ""}, "ru") == "hi"
    assert localize({"uz-Latn": "salom", "en": "hi"}, "uz-Cyrl") == "salom"
