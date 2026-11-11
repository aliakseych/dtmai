from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.modules.lyceums.application.profile import ProfileService
from app.modules.lyceums.domain.profile import REP_PROFILE_FIELDS
from app.modules.lyceums.domain.rep import (
    MembershipStatus,
    Post,
    PostKind,
    PostStatus,
    RepMembership,
    ensure_can_apply,
    parse_kind,
)
from app.modules.lyceums.ports import (
    Clock,
    LyceumProfiles,
    MembershipRepository,
    PostRepository,
    RepRoleGranter,
)
from app.shared.errors import Forbidden, NotFound, ValidationFailed
from app.shared.ids import new_id


@dataclass(frozen=True, slots=True)
class PostInput:
    kind: str
    title: str
    body: str = ""
    starts_at: datetime | None = None
    link: str | None = None


class RepService:
    def __init__(
        self,
        profiles: LyceumProfiles,
        members: MembershipRepository,
        posts: PostRepository,
        roles: RepRoleGranter,
        profile: ProfileService,
        clock: Clock,
    ) -> None:
        self._profiles, self._members, self._posts = profiles, members, posts
        self._roles, self._clock, self._profile = roles, clock, profile

    # --- membership -------------------------------------------------------
    async def _require_lyceum(self, lyceum_id: UUID) -> None:
        if not await self._profiles.exists(lyceum_id):
            raise NotFound("lyceum not found", code="lyceum_not_found")

    async def apply(
        self, user_id: UUID, lyceum_id: UUID, note: str | None, *, is_guest: bool
    ) -> RepMembership:
        await self._require_lyceum(lyceum_id)
        ensure_can_apply(await self._members.get(user_id, lyceum_id))
        membership = RepMembership.apply(user_id, lyceum_id, note, is_guest=is_guest)
        await self._members.add(membership)
        return membership

    async def membership(self, user_id: UUID, lyceum_id: UUID) -> RepMembership | None:
        return await self._members.get(user_id, lyceum_id)

    async def list_applications(self, limit: int = 100) -> list[RepMembership]:
        return await self._members.list_pending(limit)

    async def _pending(self, user_id: UUID, lyceum_id: UUID) -> RepMembership:
        m = await self._members.get(user_id, lyceum_id)
        if m is None:
            raise NotFound("application not found", code="rep_application_not_found")
        return m

    async def approve(self, user_id: UUID, lyceum_id: UUID) -> RepMembership:
        m = await self._pending(user_id, lyceum_id)
        m.approve(self._clock.now())
        await self._members.save(m)
        await self._roles.grant_lyceum_rep(user_id)
        await self._profiles.mark_verified_rep(lyceum_id)
        return m

    async def reject_application(self, user_id: UUID, lyceum_id: UUID) -> None:
        m = await self._pending(user_id, lyceum_id)
        if m.status is MembershipStatus.APPROVED:
            raise ValidationFailed("approved reps cannot be rejected", code="rep_already_approved")
        await self._members.delete(user_id, lyceum_id)

    async def _scoped(self, user_id: UUID, lyceum_id: UUID) -> RepMembership:
        m = await self._members.get(user_id, lyceum_id)
        if m is None:
            raise Forbidden("not a representative of this lyceum", code="rep_forbidden")
        m.ensure_manages(lyceum_id)
        return m

    # --- rep profile ------------------------------------------------------
    async def update_profile(
        self, user_id: UUID, lyceum_id: UUID, changes: Mapping[str, Any]
    ) -> None:
        """Approved reps edit only their own lyceum's rep-editable profile fields."""
        await self._scoped(user_id, lyceum_id)
        forbidden = set(changes) - REP_PROFILE_FIELDS
        if forbidden:
            raise Forbidden("field is not editable by representatives", code="rep_forbidden")
        await self._profile.update(lyceum_id, changes)

    # --- rep posts --------------------------------------------------------
    async def list_own(self, user_id: UUID, lyceum_id: UUID) -> list[Post]:
        await self._scoped(user_id, lyceum_id)
        return await self._posts.list_for_lyceum(lyceum_id)

    async def create_post(self, user_id: UUID, lyceum_id: UUID, data: PostInput) -> Post:
        await self._scoped(user_id, lyceum_id)
        post = Post(
            id=new_id(), lyceum_id=lyceum_id, author_id=user_id, kind=parse_kind(data.kind),
            title=data.title, body=data.body, starts_at=data.starts_at, link=data.link,
        )
        await self._posts.add(post)
        return post

    async def _own_post(self, user_id: UUID, lyceum_id: UUID, post_id: UUID) -> Post:
        await self._scoped(user_id, lyceum_id)
        post = await self._posts.get(post_id)
        if post is None or post.lyceum_id != lyceum_id:
            raise NotFound("post not found", code="post_not_found")
        return post

    async def edit_post(
        self, user_id: UUID, lyceum_id: UUID, post_id: UUID, data: PostInput
    ) -> Post:
        post = await self._own_post(user_id, lyceum_id, post_id)
        kind: PostKind = parse_kind(data.kind)
        post.rep_edit(
            kind=kind, title=data.title, body=data.body, starts_at=data.starts_at, link=data.link
        )
        await self._posts.save(post)
        return post

    async def delete_post(self, user_id: UUID, lyceum_id: UUID, post_id: UUID) -> None:
        post = await self._own_post(user_id, lyceum_id, post_id)
        await self._posts.delete(post.id)

    # --- moderation -------------------------------------------------------
    async def moderation_queue(self, status: PostStatus, limit: int = 100) -> list[Post]:
        return await self._posts.list_by_status(status, limit)

    async def moderate(self, post_id: UUID, *, publish: bool, reason: str | None) -> Post:
        post = await self._posts.get(post_id)
        if post is None:
            raise NotFound("post not found", code="post_not_found")
        if publish:
            post.publish(self._clock.now())
        else:
            post.reject(reason or "")
        await self._posts.save(post)
        return post

    async def published(self, lyceum_id: UUID, limit: int = 50) -> list[Post]:
        return await self._posts.list_published(lyceum_id, limit)
