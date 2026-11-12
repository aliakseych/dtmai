from dataclasses import replace
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from app.modules.exam_info.domain.models import (
    CertRule,
    CertRuleNotFound,
    Claim,
    ExamEvent,
    ExamEventNotFound,
    ExamProfile,
    ExamProfileNotFound,
    Exemption,
    FaqItem,
    FaqNotFound,
    SectionNotFound,
    evaluate_exemptions,
    validate_rule,
    validate_taper_days,
)
from app.modules.exam_info.ports import ExamInfoRepository, SubjectDirectory
from app.shared.errors import ValidationFailed

PROFILE_PATCHABLE = frozenset(
    {
        "exam_date",
        "date_verified",
        "verified",
        "active",
        "trust_self_declared",
        "taper_days",
        "mock_blueprint_id",
        "source_url",
        "position",
    }
)
PROFILE_NULLABLE = frozenset({"exam_date", "mock_blueprint_id", "source_url"})


class ExamInfoService:
    def __init__(self, repo: ExamInfoRepository, subjects: SubjectDirectory) -> None:
        self._repo = repo
        self._subjects = subjects

    async def _require_subjects(self, subject_ids: list[UUID]) -> None:
        known = set((await self._subjects.ids_by_code()).values())
        missing = [str(i) for i in subject_ids if i not in known]
        if missing:
            raise ValidationFailed(
                f"unknown catalog subject: {', '.join(missing)}", code="unknown_subject"
            )

    # --- profiles ---------------------------------------------------------------
    async def list_profiles(self, *, active_only: bool = True) -> list[ExamProfile]:
        return await self._repo.list_profiles(active_only=active_only)

    async def profile_for_direction(self, direction_code: str) -> ExamProfile | None:
        return await self._repo.get_profile_by_direction(direction_code, active_only=True)

    async def get_profile_by_direction(self, direction_code: str) -> ExamProfile:
        profile = await self.profile_for_direction(direction_code)
        if profile is None:
            raise ExamProfileNotFound("exam profile not found")
        return profile

    async def update_profile(self, profile_id: UUID, fields: dict[str, Any]) -> ExamProfile:
        if await self._repo.get_profile(profile_id) is None:
            raise ExamProfileNotFound("exam profile not found")
        fields = {
            k: v
            for k, v in fields.items()
            if k in PROFILE_PATCHABLE and (v is not None or k in PROFILE_NULLABLE)
        }
        if fields.get("taper_days") is not None:
            validate_taper_days(fields["taper_days"])
        await self._repo.update_profile(profile_id, fields)
        updated = await self._repo.get_profile(profile_id)
        assert updated is not None
        return updated

    async def set_section_subject(self, section_id: UUID, subject_id: UUID | None) -> None:
        if await self._repo.get_section(section_id) is None:
            raise SectionNotFound("section not found")
        if subject_id is not None:
            await self._require_subjects([subject_id])
        await self._repo.set_section_subject(section_id, subject_id)

    async def replace_choice(self, group: str, subject_ids: list[UUID]) -> None:
        await self._require_subjects(subject_ids)
        await self._repo.replace_choice(group, subject_ids)

    async def evaluate_exemptions(
        self, profile: ExamProfile, claims: list[Claim]
    ) -> list[Exemption]:
        return evaluate_exemptions(profile.sections, profile.rules, claims)

    # --- certificate rules ------------------------------------------------------------
    async def create_rule(self, section_id: UUID, **fields: Any) -> CertRule:
        section = await self._repo.get_section(section_id)
        if section is None:
            raise SectionNotFound("section not found")
        rule = CertRule(id=uuid4(), section_id=section_id, **fields)
        validate_rule(section, rule.cert_type, rule.active, rule.min_value, rule.awarded_fraction)
        await self._repo.save_rule(rule)
        return rule

    async def update_rule(self, rule_id: UUID, **fields: Any) -> CertRule:
        current = await self._repo.get_rule(rule_id)
        if current is None:
            raise CertRuleNotFound("certificate rule not found")
        section = await self._repo.get_section(current.section_id)
        assert section is not None
        rule = replace(current, **fields)
        validate_rule(section, rule.cert_type, rule.active, rule.min_value, rule.awarded_fraction)
        await self._repo.save_rule(rule)
        return rule

    async def delete_rule(self, rule_id: UUID) -> None:
        if not await self._repo.delete_rule(rule_id):
            raise CertRuleNotFound("certificate rule not found")

    # --- events ---------------------------------------------------------------------------
    async def list_events(self, exam_year: int | None = None) -> list[ExamEvent]:
        return await self._repo.list_events(exam_year)

    async def create_event(
        self,
        *,
        exam_year: int,
        kind: str,
        starts_on: date,
        ends_on: date | None,
        label: dict[str, str],
        verified: bool,
        source_url: str | None,
        position: int,
    ) -> ExamEvent:
        event = ExamEvent(
            uuid4(), exam_year, kind, starts_on, label, ends_on, verified, source_url, position
        )
        await self._repo.save_event(event)
        return event

    async def update_event(self, event_id: UUID, **fields: Any) -> ExamEvent:
        current = await self._repo.get_event(event_id)
        if current is None:
            raise ExamEventNotFound("exam event not found")
        event = replace(current, **fields)
        await self._repo.save_event(event)
        return event

    async def delete_event(self, event_id: UUID) -> None:
        if not await self._repo.delete_event(event_id):
            raise ExamEventNotFound("exam event not found")

    # --- FAQ ----------------------------------------------------------------------------------
    async def list_faq(
        self, *, published_only: bool = True, category: str | None = None
    ) -> list[FaqItem]:
        return await self._repo.list_faq(published_only=published_only, category=category)

    async def create_faq(self, *, updated_by: UUID | None, **fields: Any) -> FaqItem:
        item = FaqItem(id=uuid4(), updated_by=updated_by, **fields)
        await self._repo.save_faq(item)
        return item

    async def update_faq(self, faq_id: UUID, *, updated_by: UUID | None, **fields: Any) -> FaqItem:
        current = await self._repo.get_faq(faq_id)
        if current is None:
            raise FaqNotFound("faq item not found")
        item = replace(current, updated_by=updated_by, **fields)
        await self._repo.save_faq(item)
        return item

    async def delete_faq(self, faq_id: UUID) -> None:
        if not await self._repo.delete_faq(faq_id):
            raise FaqNotFound("faq item not found")
