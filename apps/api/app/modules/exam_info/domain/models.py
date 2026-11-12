"""Pure exam rules: sections, score math, certificate exemptions, FAQ and event invariants."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Final
from uuid import UUID

from app.shared.errors import Conflict, NotFound, ValidationFailed

LOCALES: Final = ("uz-Latn", "uz-Cyrl", "ru", "en")
DEFAULT_LOCALE: Final = "uz-Latn"
# Fallback order when a text misses the requested locale.
_FALLBACK: Final = ("uz-Latn", "en", "ru", "uz-Cyrl")

SECTION_ROLES: Final = ("iq", "subject", "creative")
CERT_TYPES: Final = ("cefr", "ielts", "toefl", "national", "other_intl")
# Foreign-language proofs; "national" applies to any exemptible subject.
LANGUAGE_CERT_TYPES: Final = frozenset({"cefr", "ielts", "toefl", "other_intl"})
EVENT_KINDS: Final = ("applications", "test", "results", "appeal")
PROFILE_KINDS: Final = ("academic_lyceum", "specialized_school")
CEFR_LEVELS: Final = ("A1", "A2", "B1", "B2", "C1", "C2")
FOREIGN_LANGUAGE_GROUP: Final = "foreign_language"

# 2027/28 academic-lyceum structure (Ministry order, Nov 2025).
LYCEUM_QUESTIONS: Final = 20
LYCEUM_SUBJECT_POINTS: Final = Decimal("3.1")
LYCEUM_IQ_POINTS: Final = Decimal("1.1")
LYCEUM_MAX_SCORE: Final = Decimal("146")


class ExamProfileNotFound(NotFound):
    code = "exam_profile_not_found"


class SectionNotFound(NotFound):
    code = "exam_section_not_found"


class FaqNotFound(NotFound):
    code = "faq_not_found"


class ExamEventNotFound(NotFound):
    code = "exam_event_not_found"


class CertRuleNotFound(NotFound):
    code = "cert_rule_not_found"


class ExamProfileInvalid(ValidationFailed):
    code = "exam_profile_invalid"


class DuplicateKey(Conflict):
    code = "duplicate_key"


def localize(texts: dict[str, str], locale: str) -> str:
    """Text for `locale`, else the first non-empty in the fallback order."""
    for loc in (locale, *_FALLBACK):
        if texts.get(loc):
            return texts[loc]
    return next((v for v in texts.values() if v), "")


def require_all_locales(texts: dict[str, str], what: str) -> dict[str, str]:
    missing = [loc for loc in LOCALES if not texts.get(loc, "").strip()]
    if missing:
        raise ValidationFailed(
            f"{what} is missing locales: {', '.join(missing)}", code="locales_missing"
        )
    return {loc: texts[loc].strip() for loc in LOCALES}


def cefr_ordinal(label: str) -> int:
    """A1=1 .. C2=6, the `min_value` scale of CEFR certificate rules."""
    try:
        return CEFR_LEVELS.index(label.strip().upper()) + 1
    except ValueError:
        raise ValidationFailed(f"unknown CEFR level: {label}", code="unknown_cefr_level") from None


@dataclass(frozen=True, slots=True)
class Section:
    id: UUID
    role: str
    slot: int
    names: dict[str, str]
    subject_id: UUID | None = None
    subject_code: str | None = None
    choice_group: str | None = None
    question_count: int | None = None
    points_per_question: Decimal | None = None
    max_points: Decimal = Decimal(0)
    exemptible: bool = True
    position: int = 0

    def __post_init__(self) -> None:
        if self.role not in SECTION_ROLES:
            raise ExamProfileInvalid(f"unknown section role: {self.role}")
        if (self.role == "iq") != (self.slot == 0):
            raise ExamProfileInvalid("slot 0 is the IQ section, and only it")
        if self.role == "iq" and self.exemptible:
            raise ExamProfileInvalid("the IQ section is never exemptible", code="iq_not_exemptible")
        if self.role == "creative":
            if self.question_count is not None or self.points_per_question is not None:
                raise ExamProfileInvalid(
                    "a creative section has no question count or points per question"
                )
            if self.exemptible:
                raise ExamProfileInvalid("a creative section is never exemptible")
        elif self.question_count is None or self.points_per_question is None:
            raise ExamProfileInvalid("a test section needs question_count and points_per_question")
        elif self.max_points != self.question_count * self.points_per_question:
            raise ExamProfileInvalid("max_points must equal question_count * points_per_question")

    @property
    def is_foreign_language(self) -> bool:
        return self.choice_group == FOREIGN_LANGUAGE_GROUP

    @property
    def in_app(self) -> bool:
        """Creative exams are not a test: the app cannot prepare for them."""
        return self.role != "creative"

    @property
    def available(self) -> bool:
        """The app can prepare for it: not a creative exam and its subject is in the catalog.

        A choice-group section counts as available; its options are catalog subjects. IQ is
        always served (it has its own catalog subject).
        """
        if not self.in_app:
            return False
        return self.role == "iq" or self.subject_id is not None or self.choice_group is not None


@dataclass(frozen=True, slots=True)
class CertRule:
    id: UUID
    section_id: UUID
    cert_type: str
    language_subject_id: UUID | None = None
    level_label: str | None = None
    min_value: Decimal | None = None
    awarded_fraction: Decimal = Decimal(1)
    note: dict[str, str] = field(default_factory=dict)
    verified: bool = False
    source_url: str | None = None
    active: bool = True


@dataclass(frozen=True, slots=True)
class ExamProfile:
    id: UUID
    code: str
    kind: str
    names: dict[str, str]
    exam_year: int
    max_score: Decimal
    direction_code: str | None = None
    group_code: str | None = None
    exam_date: date | None = None
    date_verified: bool = False
    trust_self_declared: bool = False
    taper_days: int = 6
    mock_blueprint_id: UUID | None = None
    source_url: str | None = None
    verified: bool = False
    active: bool = True
    position: int = 0
    sections: tuple[Section, ...] = ()
    rules: tuple[CertRule, ...] = ()
    choices: dict[str, tuple[UUID, ...]] = field(default_factory=dict)

    def section(self, section_id: UUID) -> Section:
        for s in self.sections:
            if s.id == section_id:
                return s
        raise SectionNotFound("section not found in this profile")

    @property
    def planned_sections(self) -> tuple[Section, ...]:
        return tuple(s for s in self.sections if s.in_app)


def validate_taper_days(days: int) -> int:
    if not 5 <= days <= 7:
        raise ExamProfileInvalid("taper_days must be 5..7", code="taper_days_out_of_range")
    return days


def total_points(sections: tuple[Section, ...] | list[Section]) -> Decimal:
    return sum((s.max_points for s in sections), Decimal(0))


def validate_profile(profile: ExamProfile) -> None:
    """Sections must have distinct slots and add up to the profile max score."""
    slots = [s.slot for s in profile.sections]
    if len(set(slots)) != len(slots):
        raise ExamProfileInvalid("duplicate section slot")
    if total_points(profile.sections) != profile.max_score:
        raise ExamProfileInvalid("sections must add up to max_score", code="score_mismatch")
    validate_taper_days(profile.taper_days)


def validate_rule(
    section: Section, cert_type: str, active: bool, min_value: Decimal | None, fraction: Decimal
) -> None:
    if cert_type not in CERT_TYPES:
        raise ValidationFailed(f"unknown cert_type: {cert_type}", code="unknown_cert_type")
    if section.role == "iq" or not section.exemptible:
        raise ValidationFailed("this section can never be exempt", code="section_not_exemptible")
    if section.role != "subject":
        raise ValidationFailed("only test subjects can be exempt", code="section_not_exemptible")
    if cert_type in LANGUAGE_CERT_TYPES and not section.is_foreign_language:
        raise ValidationFailed(
            f"{cert_type} certificates apply to foreign-language sections only",
            code="cert_type_not_allowed",
        )
    if active and min_value is None:
        raise ValidationFailed("an active rule needs min_value", code="min_value_required")
    if not Decimal(0) <= fraction <= Decimal(1):
        raise ValidationFailed("awarded_fraction must be within 0..1", code="fraction_out_of_range")


@dataclass(frozen=True, slots=True)
class Claim:
    """A certificate the learner says they hold."""

    section_id: UUID
    cert_type: str
    value: Decimal
    language_subject_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Exemption:
    section_id: UUID
    rule_id: UUID
    fraction: Decimal
    points: Decimal


def _rule_accepts(rule: CertRule, section: Section, claim: Claim) -> bool:
    if not rule.active or rule.min_value is None or rule.cert_type != claim.cert_type:
        return False
    if rule.cert_type in LANGUAGE_CERT_TYPES and not section.is_foreign_language:
        return False
    if rule.language_subject_id not in (None, claim.language_subject_id):
        return False
    return claim.value >= rule.min_value


def evaluate_exemptions(
    sections: tuple[Section, ...], rules: tuple[CertRule, ...], claims: list[Claim]
) -> list[Exemption]:
    """One exemption per section (the best-paying matching rule). IQ and creative never qualify."""
    by_id = {s.id: s for s in sections}
    best: dict[UUID, Exemption] = {}
    for claim in claims:
        section = by_id.get(claim.section_id)
        if section is None or section.role != "subject" or not section.exemptible:
            continue
        for rule in rules:
            if rule.section_id != section.id or not _rule_accepts(rule, section, claim):
                continue
            points = section.max_points * rule.awarded_fraction
            if section.id not in best or points > best[section.id].points:
                best[section.id] = Exemption(section.id, rule.id, rule.awarded_fraction, points)
    return sorted(best.values(), key=lambda e: by_id[e.section_id].slot)


def projected_score(
    sections: tuple[Section, ...], exemptions: list[Exemption], earned: dict[UUID, Decimal]
) -> Decimal:
    """Exempt sections count their awarded points; others count `earned` capped at max_points."""
    exempt = {e.section_id: e.points for e in exemptions}
    total = Decimal(0)
    for s in sections:
        total += exempt[s.id] if s.id in exempt else min(earned.get(s.id, Decimal(0)), s.max_points)
    return total


@dataclass(frozen=True, slots=True)
class ExamEvent:
    id: UUID
    exam_year: int
    kind: str
    starts_on: date
    label: dict[str, str]
    ends_on: date | None = None
    verified: bool = False
    source_url: str | None = None
    position: int = 0

    def __post_init__(self) -> None:
        if self.kind not in EVENT_KINDS:
            raise ValidationFailed(f"unknown event kind: {self.kind}", code="unknown_event_kind")
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValidationFailed("ends_on is before starts_on", code="event_range_invalid")


@dataclass(frozen=True, slots=True)
class FaqItem:
    id: UUID
    key: str
    category: str
    question: dict[str, str]
    answer: dict[str, str]
    position: int = 0
    published: bool = True
    source_url: str | None = None
    verified: bool = False
    updated_at: datetime | None = None
    updated_by: UUID | None = None

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.category.strip():
            raise ValidationFailed("key and category are required", code="faq_key_required")
        require_all_locales(self.question, "question")
        require_all_locales(self.answer, "answer")
