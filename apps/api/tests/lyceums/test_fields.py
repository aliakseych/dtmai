import asyncio
from uuid import uuid4

import pytest

from app.modules.lyceums.application.profile import ProfileService
from app.modules.lyceums.domain.fields import (
    MAX_FIELD_SUBJECTS,
    normalize_speciality_code,
    validate_field_subject_ids,
)
from app.modules.lyceums.domain.profile import CityView
from app.shared.errors import ValidationFailed


def test_code_trimmed_and_bounded():
    assert normalize_speciality_code(" 60110100 ") == "60110100"
    for bad in ("", "   ", "x" * 21):
        with pytest.raises(ValidationFailed) as e:
            normalize_speciality_code(bad)
        assert e.value.code == "invalid_field_code"


def test_subjects_deduped_in_order():
    a, b = uuid4(), uuid4()
    assert validate_field_subject_ids([b, a, b]) == [b, a]
    assert validate_field_subject_ids([]) == []


def test_too_many_subjects():
    with pytest.raises(ValidationFailed) as e:
        validate_field_subject_ids([uuid4() for _ in range(MAX_FIELD_SUBJECTS + 1)])
    assert e.value.code == "too_many_subjects"


class Cities:
    def __init__(self) -> None:
        self.locale = None

    async def list_with_counts(self, locale):
        self.locale = locale
        return [CityView("a", {"ru": "Б"}, 1)]


def test_cities_request_locale_is_forwarded():
    cities = Cities()
    asyncio.run(ProfileService(None, cities).cities("ru"))  # type: ignore[arg-type]
    assert cities.locale == "ru"
