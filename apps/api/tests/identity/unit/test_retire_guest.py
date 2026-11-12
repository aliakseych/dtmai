import pytest

from app.modules.identity.domain.models import Role, User
from app.shared.errors import Forbidden
from app.shared.ids import new_id
from tests.identity.unit.test_password_reset import make


async def test_retire_guest_disables_and_revokes():
    g = User(id=new_id(), name="G", roles={Role.GUEST})
    svc, users, _, _ = make(g)
    await svc.retire_guest(g.id)
    assert users.u.disabled
    assert svc._refresh.revoked_for == [g.id]


async def test_retire_rejects_non_guest():
    u = User(id=new_id(), name="U", email="u@b.uz", roles={Role.STUDENT})
    svc, _, _, _ = make(u)
    with pytest.raises(Forbidden):
        await svc.retire_guest(u.id)


async def test_retire_guest_carries_profile_into_target():
    lyc, lang = new_id(), new_id()
    g = User(
        id=new_id(),
        name="G",
        roles={Role.GUEST},
        dream_lyceum_ids=[lyc],
        education_language_id=lang,
        city="tashkent",
        field_code="x",
        subject_ids=[new_id()],
    )
    target = User(id=new_id(), name="T", email="t@b.uz", roles={Role.STUDENT})
    svc, users, _, _ = make(g)
    svc._users.get = lambda uid: _get(uid, g, target)
    await svc.retire_guest(g.id, target.id)
    assert target.dream_lyceum_ids == [lyc] and target.education_language_id == lang
    assert (
        target.city == "tashkent"
        and target.field_code == "x"
        and target.subject_ids == g.subject_ids
    )


async def _get(uid, *users):
    return next(u for u in users if u.id == uid)
