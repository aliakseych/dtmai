"""Exam structure as the planner needs it (a snapshot of the admin-managed exam profile)."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

ROLE_IQ = "iq"
ROLE_CREATIVE = "creative"


@dataclass(frozen=True, slots=True)
class ExamSection:
    section_id: UUID
    role: str  # iq | subject | creative
    subject_id: UUID | None  # None: choice group (see subject_options) or no catalog subject yet
    max_points: float
    exemptible: bool
    choice_group: str | None = None
    subject_options: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class CertRule:
    section_id: UUID
    cert_type: str
    min_value: float | None
    awarded_fraction: float
    language_subject_id: UUID | None = None
    active: bool = True


@dataclass(frozen=True, slots=True)
class ExamProfile:
    code: str
    direction_code: str | None
    exam_date: date | None
    max_score: float
    taper_days: int
    mock_blueprint_id: UUID | None
    sections: tuple[ExamSection, ...]
    cert_rules: tuple[CertRule, ...]
    date_verified: bool = False  # the exam date is confirmed, not an estimate


@dataclass(frozen=True, slots=True)
class Certificate:
    """A learner's claim, e.g. IELTS 6.0 for the foreign-language section."""

    section_id: UUID
    cert_type: str
    value: float
    language_subject_id: UUID | None = None


def resolve_subject(section: ExamSection, chosen: UUID | None) -> UUID | None:
    """Catalog subject a section is studied through; None when the app has no content for it."""
    if section.role == ROLE_CREATIVE:
        return None
    if section.subject_id is not None:
        return section.subject_id
    if chosen is not None and chosen in section.subject_options:
        return chosen
    return None


def exemptions(
    sections: tuple[ExamSection, ...], rules: tuple[CertRule, ...], claims: tuple[Certificate, ...]
) -> dict[UUID, float]:
    """section_id -> awarded fraction for fully exempt sections. IQ is never exempt.

    A claim exempts a section when an active rule of the same type is met (`value >= min_value`,
    same language when the rule names one) at full points (`awarded_fraction == 1`).
    """
    out: dict[UUID, float] = {}
    for section in sections:
        if not section.exemptible or section.role == ROLE_IQ:
            continue
        for rule in rules:
            if rule.section_id != section.section_id or not rule.active or rule.min_value is None:
                continue
            if rule.awarded_fraction < 1:
                continue
            if any(_meets(rule, c) for c in claims if c.section_id == section.section_id):
                out[section.section_id] = rule.awarded_fraction
                break
    return out


def _meets(rule: CertRule, claim: Certificate) -> bool:
    if claim.cert_type != rule.cert_type or rule.min_value is None or claim.value < rule.min_value:
        return False
    return rule.language_subject_id is None or rule.language_subject_id == claim.language_subject_id
