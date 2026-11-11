import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.modules.lyceums.domain.admission import (
    PlanRow,
    Seats,
    admission_competition,
    normalize_phone,
    normalize_telegram,
    validate_phones,
    validate_seats,
)
from app.modules.lyceums.domain.matching import match_names, name_tokens
from app.shared.errors import ValidationFailed

SEED = Path(__file__).resolve().parents[2] / "app/modules/lyceums/seed"


def test_seed_totals_match_the_order() -> None:
    doc = json.loads((SEED / "admission_plan_2026.json").read_text("utf-8"))
    assert len(doc["lyceums"]) == 69
    seats = [d["seats"] for e in doc["lyceums"] for d in e["directions"]]
    assert [sum(s[k] for s in seats) for k in ("total", "uz", "ru", "qq")] == [
        14898,
        12116,
        2340,
        442,
    ]
    assert all(s["total"] == s["uz"] + s["ru"] + s["qq"] for s in seats)


def test_seed_contacts_are_well_formed() -> None:
    doc = json.loads((SEED / "contacts.json").read_text("utf-8"))
    assert len(doc["lyceums"]) == 69
    for e in doc["lyceums"]:
        for p in e["phones"]:
            assert p.startswith("+998") and len(p) == 13 and p[1:].isdigit()
        assert e["telegram"] is None or e["telegram"].startswith("https://t.me/")


def test_validate_seats() -> None:
    assert validate_seats(10, 5, 1).total == 16
    with pytest.raises(ValidationFailed):
        validate_seats(-1, 0, 0)


def test_phone_and_telegram_normalization() -> None:
    assert normalize_phone("90 123-45-67") == "+998901234567"
    assert normalize_phone("+998 (90) 123-45-67") == "+998901234567"
    assert normalize_telegram("@dtm_ai") == "https://t.me/dtm_ai"
    assert normalize_telegram(None) is None
    with pytest.raises(ValidationFailed):
        validate_phones(["12"])


def test_matcher_bridges_cyrillic_and_typos() -> None:
    sources = {
        1: "Toshent shahar akademik litseyi",
        2: "Qarshi shahar 2- son akademik litseyi",
        3: "Нуристон академик лицейи",
    }
    db = {
        "a": "Toshkent shahar akademik litseyi",
        "b": "Qarshi shahar 2-son akademik litseyi",
        "c": "Nuriston akademik litseyi",
        "d": "Qarshi shahar akademik litseyi",
    }
    result = match_names(sources, db)
    assert result.matched == {1: "a", 2: "b", 3: "c"}


def test_matcher_does_not_conflate_numbers() -> None:
    result = match_names({1: "Qarshi 2-son litseyi"}, {"x": "Qarshi 3-son litseyi"})
    assert result.matched == {}
    assert name_tokens("2- son") == name_tokens("2-son")


def test_competition_per_direction_with_lyceum_fallback() -> None:
    lid = uuid4()
    plan = [
        PlanRow(lid, 2026, "3910001", None, Seats(10, 0, 0)),
        PlanRow(lid, 2026, "3920001", None, Seats(10, 0, 0)),
    ]
    stats = [(2025, "3910001", 30), (2025, "9999999", 20), (2024, "3910001", 999)]
    comp = admission_competition(plan, stats)
    by_code = {d.direction_code: d for d in comp.directions}
    assert by_code["3910001"].ratio == 3.0
    assert by_code["3920001"].ratio is None
    assert comp.lyceum_ratio == 2.5
    assert comp.applications_year == 2025


def test_competition_without_seats_has_no_ratio() -> None:
    comp = admission_competition([], [(2025, "3910001", 30)])
    assert comp.lyceum_ratio is None
