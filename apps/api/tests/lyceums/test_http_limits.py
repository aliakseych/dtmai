import pytest
from pydantic import ValidationError

from app.interfaces.http.v1.billing import GrantIn, PlanCreate
from app.interfaces.http.v1.exam_info import FaqIn
from app.interfaces.http.v1.lyceums import RepProfilePatch


def test_rep_profile_caps():
    with pytest.raises(ValidationError):
        RepProfilePatch(courses=["x"] * 51)
    with pytest.raises(ValidationError):
        RepProfilePatch(courses=["x" * 201])
    with pytest.raises(ValidationError):
        RepProfilePatch(description={"en": "x" * 5001})
    with pytest.raises(ValidationError):
        RepProfilePatch(contacts={"email": "e" * 400})


def test_plan_and_grant_bounds():
    for months in (0, 37):
        with pytest.raises(ValidationError):
            GrantIn(user_id="00000000-0000-0000-0000-000000000001", plan_code="p", months=months)
        with pytest.raises(ValidationError):
            PlanCreate(code="p", names={}, price_uzs=1, period_months=months)


def test_source_url_scheme_and_length():
    base = dict(key="k", category="c", question={"en": "q"}, answer={"en": "a"})
    FaqIn(**base, source_url="https://example.uz/x")
    for bad in ("javascript:alert(1)", "ftp://x", "https://x/" + "a" * 2050):
        with pytest.raises(ValidationError):
            FaqIn(**base, source_url=bad)
