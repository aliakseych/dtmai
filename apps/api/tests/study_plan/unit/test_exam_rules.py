from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.modules.study_plan.domain.exam import (
    ROLE_CREATIVE,
    ROLE_IQ,
    Certificate,
    CertRule,
    ExamSection,
    exemptions,
)
from app.modules.study_plan.domain.models import PlanSettings
from app.modules.study_plan.domain.prediction import countdown, predicted_score
from app.shared.errors import ValidationFailed

ENG, MATH, IQ_S, DRAW = uuid4(), uuid4(), uuid4(), uuid4()
SECTIONS = (
    ExamSection(ENG, "subject", uuid4(), 62.0, True),
    ExamSection(MATH, "subject", uuid4(), 62.0, False),
    ExamSection(IQ_S, ROLE_IQ, uuid4(), 22.0, True),
    ExamSection(DRAW, ROLE_CREATIVE, None, 30.0, False),
)
RULES = (
    CertRule(ENG, "ielts", 6.0, 1.0),
    CertRule(IQ_S, "ielts", 1.0, 1.0),
    CertRule(ENG, "cefr", 5.0, 0.8),
)


def test_cert_exempts_at_full_points() -> None:
    assert exemptions(SECTIONS, RULES, (Certificate(ENG, "ielts", 6.5),)) == {ENG: 1.0}


def test_below_threshold_or_partial_not_exempt() -> None:
    assert exemptions(SECTIONS, RULES, (Certificate(ENG, "ielts", 5.5),)) == {}
    assert exemptions(SECTIONS, RULES, (Certificate(ENG, "cefr", 6.0),)) == {}


def test_iq_never_exempt() -> None:
    assert exemptions(SECTIONS, RULES, (Certificate(IQ_S, "ielts", 9.0),)) == {}


def test_non_exemptible_and_inactive() -> None:
    rules = (CertRule(MATH, "x", 1.0, 1.0), CertRule(ENG, "ielts", 6.0, 1.0, active=False))
    claims = (Certificate(MATH, "x", 9), Certificate(ENG, "ielts", 9))
    assert exemptions(SECTIONS, rules, claims) == {}


def test_language_specific_rule() -> None:
    lang = uuid4()
    rules = (CertRule(ENG, "ielts", 6.0, 1.0, language_subject_id=lang),)
    assert exemptions(SECTIONS, rules, (Certificate(ENG, "ielts", 7, uuid4()),)) == {}
    assert exemptions(SECTIONS, rules, (Certificate(ENG, "ielts", 7, lang),)) == {ENG: 1.0}


def test_prediction_bounds_and_exempt() -> None:
    full = {s.subject_id: 1.0 for s in SECTIONS if s.subject_id}
    assert predicted_score(SECTIONS, {}, full, {}, 146.0) == 146.0
    assert predicted_score(SECTIONS, {}, {}, {}, 146.0) == 0.0
    assert predicted_score(SECTIONS, {ENG: 1.0}, {}, {}, 146.0) == 62.0
    over = {s.subject_id: 5.0 for s in SECTIONS if s.subject_id}
    assert predicted_score(SECTIONS, {}, over, {}, 146.0) <= 146.0


def test_countdown_phases() -> None:
    exam = date(2027, 7, 25)
    assert countdown(date(2027, 7, 1), exam, 6).phase == "preparing"
    assert countdown(date(2027, 7, 1), exam, 6).days_left == 24
    assert countdown(date(2027, 7, 22), exam, 6).phase == "taper"
    c = countdown(date(2027, 8, 1), exam, 6)
    assert c.phase == "exam_over" and c.days_left == 0
    assert c.plan_end == date(2027, 7, 19)


def _settings(**kw) -> PlanSettings:
    base = dict(
        direction_code="x", language="uz", start_date=date(2027, 1, 1), exam_date=date(2027, 7, 25)
    )
    base.update(kw)
    return PlanSettings(**base)


def test_settings_validation() -> None:
    _settings()
    for bad in (
        {"language": "en"},
        {"minutes_school_day": 5},
        {"minutes_weekend_day": 400},
        {"exam_date": date(2026, 1, 1)},
        {"target_lyceum_ids": tuple(uuid4() for _ in range(4))},
    ):
        with pytest.raises(ValidationFailed):
            _settings(**bad)


def test_settings_horizon_cap() -> None:
    start = date(2027, 1, 1)
    _settings(start_date=start, exam_date=start + timedelta(days=400))
    with pytest.raises(ValidationFailed) as e:
        _settings(start_date=start, exam_date=start + timedelta(days=401))
    assert e.value.code == "exam_date_too_far"


def test_settings_json_roundtrip() -> None:
    s = _settings(certificates=(Certificate(ENG, "ielts", 6.5),), target_lyceum_ids=(uuid4(),))
    assert PlanSettings.from_json(s.to_json()) == s
