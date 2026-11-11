import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.modules.lyceums.application.rep import PostInput, RepService
from app.modules.lyceums.domain.rep import (
    MembershipStatus,
    Post,
    PostKind,
    PostStatus,
    RepMembership,
    validate_contacts,
    validate_description,
)
from app.shared.errors import Conflict, Forbidden, NotFound, ValidationFailed

NOW = datetime(2026, 11, 14, tzinfo=UTC)
L1, L2 = uuid4(), uuid4()


class Profiles:
    def __init__(self) -> None:
        self.verified: set[UUID] = set()

    async def exists(self, lyceum_id: UUID) -> bool:
        return lyceum_id in (L1, L2)

    async def mark_verified_rep(self, lyceum_id: UUID) -> None:
        self.verified.add(lyceum_id)


class Members:
    def __init__(self) -> None:
        self.rows: dict[tuple[UUID, UUID], RepMembership] = {}

    async def get(self, u, l):
        return self.rows.get((u, l))

    async def add(self, m):
        self.rows[(m.user_id, m.lyceum_id)] = m

    async def save(self, m):
        self.rows[(m.user_id, m.lyceum_id)] = m

    async def delete(self, u, l):
        self.rows.pop((u, l), None)

    async def list_pending(self, limit):
        return [m for m in self.rows.values() if m.status is MembershipStatus.PENDING]


class Posts:
    def __init__(self) -> None:
        self.rows: dict[UUID, Post] = {}

    async def add(self, p):
        self.rows[p.id] = p

    async def get(self, i):
        return self.rows.get(i)

    async def save(self, p):
        self.rows[p.id] = p

    async def delete(self, i):
        self.rows.pop(i, None)

    async def list_for_lyceum(self, l):
        return [p for p in self.rows.values() if p.lyceum_id == l]

    async def list_published(self, l, limit):
        return [p for p in self.rows.values() if p.lyceum_id == l and p.status is PostStatus.PUBLISHED]

    async def list_by_status(self, s, limit):
        return [p for p in self.rows.values() if p.status is s]


class Roles:
    def __init__(self) -> None:
        self.granted: list[UUID] = []

    async def grant_lyceum_rep(self, user_id):
        self.granted.append(user_id)


class Clock:
    def now(self):
        return NOW


def make():
    profiles, roles = Profiles(), Roles()
    return RepService(profiles, Members(), Posts(), roles, Clock()), profiles, roles


def run(coro):
    return asyncio.run(coro)


def post_in(**kw):
    base = dict(kind="announcement", title="Open day", body="Welcome")
    return PostInput(**{**base, **kw})


async def approved(svc, user, lyceum=L1):
    await svc.apply(user, lyceum, None, is_guest=False)
    await svc.approve(user, lyceum)


# --- membership ---------------------------------------------------------------
def test_guest_cannot_apply():
    svc, _, _ = make()
    with pytest.raises(Forbidden):
        run(svc.apply(uuid4(), L1, None, is_guest=True))


def test_apply_unknown_lyceum():
    svc, _, _ = make()
    with pytest.raises(NotFound):
        run(svc.apply(uuid4(), uuid4(), None, is_guest=False))


def test_double_apply_conflicts():
    svc, _, _ = make()
    u = uuid4()
    run(svc.apply(u, L1, None, is_guest=False))
    with pytest.raises(Conflict):
        run(svc.apply(u, L1, None, is_guest=False))


def test_approve_grants_role_and_verifies():
    svc, profiles, roles = make()
    u = uuid4()
    run(approved(svc, u))
    assert roles.granted == [u] and L1 in profiles.verified
    with pytest.raises(Conflict):
        run(svc.approve(u, L1))


def test_reject_application_removes_it():
    svc, _, _ = make()
    u = uuid4()
    run(svc.apply(u, L1, None, is_guest=False))
    run(svc.reject_application(u, L1))
    assert run(svc.membership(u, L1)) is None


# --- rep scoping --------------------------------------------------------------
def test_pending_rep_cannot_post():
    svc, _, _ = make()
    u = uuid4()
    run(svc.apply(u, L1, None, is_guest=False))
    with pytest.raises(Forbidden):
        run(svc.create_post(u, L1, post_in()))


def test_stranger_cannot_post():
    svc, _, _ = make()
    with pytest.raises(Forbidden):
        run(svc.create_post(uuid4(), L1, post_in()))


def test_rep_scoped_to_own_lyceum():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u, L1))
    with pytest.raises(Forbidden):
        run(svc.create_post(u, L2, post_in()))
    p = run(svc.create_post(u, L1, post_in()))
    other = uuid4()
    run(approved(svc, other, L2))
    with pytest.raises(NotFound):
        run(svc.edit_post(other, L2, p.id, post_in()))  # post belongs to L1


# --- posts / moderation --------------------------------------------------------
def test_rep_post_starts_pending_and_hidden():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    assert p.status is PostStatus.PENDING
    assert run(svc.published(L1)) == []


def test_publish_then_visible_and_edit_requeues():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    run(svc.moderate(p.id, publish=True, reason=None))
    assert [x.id for x in run(svc.published(L1))] == [p.id]
    assert p.published_at == NOW
    run(svc.edit_post(u, L1, p.id, post_in(title="New")))
    assert p.status is PostStatus.PENDING and run(svc.published(L1)) == []


def test_reject_requires_reason_and_edit_clears_it():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    with pytest.raises(ValidationFailed):
        run(svc.moderate(p.id, publish=False, reason="  "))
    run(svc.moderate(p.id, publish=False, reason="spam"))
    assert p.status is PostStatus.REJECTED and p.reject_reason == "spam"
    with pytest.raises(Conflict):
        run(svc.moderate(p.id, publish=True, reason=None))
    run(svc.edit_post(u, L1, p.id, post_in()))
    assert p.status is PostStatus.PENDING and p.reject_reason is None


def test_published_can_be_taken_down():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    run(svc.moderate(p.id, publish=True, reason=None))
    run(svc.moderate(p.id, publish=False, reason="outdated"))
    assert p.status is PostStatus.REJECTED
    with pytest.raises(Conflict):
        run(svc.moderate(p.id, publish=True, reason=None))


def test_double_publish_conflicts():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    run(svc.moderate(p.id, publish=True, reason=None))
    with pytest.raises(Conflict):
        run(svc.moderate(p.id, publish=True, reason=None))


@pytest.mark.parametrize(
    "kw",
    [
        dict(kind="nope"),
        dict(title="  "),
        dict(kind="event"),  # needs starts_at
        dict(kind="chat_link"),  # needs link
        dict(link="javascript:alert(1)"),
    ],
)
def test_post_validation(kw):
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    with pytest.raises(ValidationFailed):
        run(svc.create_post(u, L1, post_in(**kw)))


def test_timed_kind_ok_with_start():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in(kind="event", starts_at=NOW)))
    assert p.kind is PostKind.EVENT


def test_delete_scoped():
    svc, _, _ = make()
    u = uuid4()
    run(approved(svc, u))
    p = run(svc.create_post(u, L1, post_in()))
    run(svc.delete_post(u, L1, p.id))
    with pytest.raises(NotFound):
        run(svc.delete_post(u, L1, p.id))


# --- profile validation ---------------------------------------------------------
def test_description_locales():
    assert validate_description({"ru": " привет ", "en": " "}) == {"ru": "привет"}
    with pytest.raises(ValidationFailed):
        validate_description({"de": "x"})


def test_contacts_keys():
    assert validate_contacts({"phone": " +998 ", "email": ""}) == {"phone": "+998"}
    with pytest.raises(ValidationFailed):
        validate_contacts({"fax": "1"})
