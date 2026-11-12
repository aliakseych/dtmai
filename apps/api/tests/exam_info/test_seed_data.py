from decimal import Decimal

from app.modules.exam_info.domain.models import LOCALES, Section
from app.modules.exam_info.infrastructure import seed_data as d


def _sections(p: d.ProfileSpec) -> list[Section]:
    return [
        Section(
            s.id,
            s.role,
            s.slot,
            s.names,
            None,
            s.subject_code,
            s.choice_group,
            s.question_count,
            s.points_per_question,
            s.max_points,
            s.exemptible,
        )  # fmt: skip
        for s in p.sections
    ]


def test_thirteen_profiles_with_unique_directions() -> None:
    specs = d.profile_specs()
    assert len(specs) == 13
    assert len({p.direction_code for p in specs}) == 13
    assert len({p.id for p in specs}) == 13


def test_every_profile_sums_to_146_and_builds_valid_sections() -> None:
    for p in d.profile_specs():
        sections = _sections(p)  # runs section invariants
        assert sum((s.max_points for s in sections), Decimal(0)) == Decimal(146), p.code
        iq = [s for s in sections if s.role == "iq"]
        assert len(iq) == 1 and iq[0].slot == 0 and iq[0].max_points == Decimal(22)
        assert not iq[0].exemptible


def test_only_aniq_3_has_a_creative_section() -> None:
    creative = [
        p.direction_code for p in d.profile_specs() if any(s.role == "creative" for s in p.sections)
    ]
    assert creative == ["3910003"]


def test_foreign_language_sections_use_choice_group() -> None:
    for p in d.profile_specs():
        for s in p.sections:
            assert (s.label_key == "foreign") == (s.choice_group == "foreign_language")
            if s.label_key == "foreign":
                assert s.subject_code is None


def test_texts_cover_all_locales() -> None:
    for p in d.profile_specs():
        assert set(p.names) == set(LOCALES)
        for s in p.sections:
            assert all(s.names[loc] for loc in LOCALES)
    for f in d.FAQ:
        assert all(f.question[loc] and f.answer[loc] for loc in LOCALES), f.key
    for e in d.EVENTS:
        assert all(e.label[loc] for loc in LOCALES)
    assert len({f.key for f in d.FAQ}) == len(d.FAQ)


def test_uz_latn_apostrophes_follow_house_rule() -> None:
    for f in d.FAQ:
        text = f.question["uz-Latn"] + f.answer["uz-Latn"]
        assert "'" not in text and "’" not in text


def test_no_cert_rule_for_iq_and_active_rules_have_minimum() -> None:
    assert all(c.min_value is not None for c in d.LANGUAGE_CERTS if c.active)
    assert d.SUBJECT_CERT.min_value is None and not d.SUBJECT_CERT.active
