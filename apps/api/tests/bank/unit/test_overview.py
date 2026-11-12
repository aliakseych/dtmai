from types import SimpleNamespace
from uuid import uuid4

from app.interfaces.http.v1.bank import build_overview
from app.modules.bank.domain.models import level_of
from app.modules.bank.facade import FacetRow


def test_level_of() -> None:
    assert [level_of(x) for x in (900, 1100, 1349, 1350)] == ["easy", "medium", "medium", "hard"]


def test_overview_filters_and_hides_inactive_bases() -> None:
    topic, ty, b1, b2, b3 = (uuid4() for _ in range(5))
    rows = [
        FacetRow(topic, ty, b1, "easy", 4, 3),
        FacetRow(topic, ty, b1, "hard", 2, 0),
        FacetRow(topic, ty, b2, "easy", 5, 1),
        FacetRow(topic, ty, None, "medium", 1, 1),
    ]
    bases = [
        {"id": b1, "code": "a", "names": {}, "kind": "custom", "year": 2024, "active": True},
        {"id": b2, "code": "b", "names": {}, "kind": "custom", "active": False},
        {"id": b3, "code": "c", "names": {}, "kind": "custom", "active": True},  # empty
    ]
    types = {ty: SimpleNamespace(names={"en": "t"}, kind="single_choice")}
    o = build_overview(rows, bases=bases, types=types, source_id=None, level=None)
    assert [b.id for b in o.bases] == [b1]
    assert (o.total, o.solved) == (12, 5)
    o = build_overview(rows, bases=bases, types=types, source_id=b1, level="hard")
    assert (o.total, o.solved, o.easy, o.hard) == (2, 0, 4, 2)
    assert len(o.bases) == 1
