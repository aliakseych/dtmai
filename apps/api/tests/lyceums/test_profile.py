import pytest

from app.modules.lyceums.domain.profile import (
    normalize_city_code,
    parse_dormitory_status,
    validate_dormitory_description,
)
from app.shared.errors import Forbidden, ValidationFailed

from .test_rep import L1, L2, approved, make, run
from uuid import uuid4


def test_dormitory_status_values():
    assert parse_dormitory_status("limited").value == "limited"
    with pytest.raises(ValidationFailed) as e:
        parse_dormitory_status("maybe")
    assert e.value.code == "invalid_dormitory_status"


def test_dormitory_description_locales():
    assert validate_dormitory_description({"en": " Rooms "}) == {"en": "Rooms"}
    with pytest.raises(ValidationFailed) as e:
        validate_dormitory_description({"de": "x"})
    assert e.value.code == "invalid_locale"


def test_city_code_normalised():
    assert normalize_city_code(None) is None
    assert normalize_city_code(" Tashkent ") == "tashkent"
    with pytest.raises(ValidationFailed) as e:
        normalize_city_code("bad code!")
    assert e.value.code == "invalid_city"


def test_rep_updates_dormitory_and_description():
    svc, profiles, _ = make()
    u = uuid4()
    run(approved(svc, u))
    run(svc.update_profile(u, L1, {"dormitory_status": "available", "courses": ["Math"]}))
    assert profiles.updated[L1] == {"dormitory_status": "available", "courses": ["Math"]}


def test_rep_profile_requires_approval():
    svc, _, _ = make()
    u = uuid4()
    with pytest.raises(Forbidden) as e:
        run(svc.update_profile(u, L1, {"dormitory_status": "none"}))
    assert e.value.code == "rep_forbidden"
    run(svc.apply(u, L1, None, is_guest=False))
    with pytest.raises(Forbidden) as e:
        run(svc.update_profile(u, L1, {"dormitory_status": "none"}))
    assert e.value.code == "rep_forbidden"


def test_rep_cannot_edit_other_lyceum():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u, L1))
    with pytest.raises(Forbidden) as e:
        run(svc.update_profile(u, L2, {"dormitory_status": "none"}))
    assert e.value.code == "rep_forbidden"


def test_rep_cannot_edit_admin_fields():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    with pytest.raises(Forbidden) as e:
        run(svc.update_profile(u, L1, {"verified_rep": True}))
    assert e.value.code == "rep_forbidden"


def test_admin_profile_city_validation():
    svc, profiles, _ = make()
    from app.modules.lyceums.application.profile import ProfileService
    from .test_rep import Cities
    ps = ProfileService(profiles, Cities())
    assert run(ps.update(L1, {"city": "tashkent"})) == ["city"]
    assert run(ps.update(L1, {"city": None})) == ["city"]
    with pytest.raises(ValidationFailed) as e:
        run(ps.update(L1, {"city": "atlantis"}))
    assert e.value.code == "unknown_city"
