from app.modules.catalog.domain.progress import Progress, derive_path_progress
from app.shared.locale import pick_locale


def states(rows):
    return [[p.state for p in r] for r in rows]


def test_fresh_path_first_open_rest_locked():
    lessons, units = derive_path_progress([[False, False], [False]])
    assert states(lessons) == [["open", "locked"], ["locked"]]
    assert [u.state for u in units] == ["open", "locked"]


def test_sequential_unlock_and_unit_done():
    lessons, units = derive_path_progress([[True, True], [True, False], [False]])
    assert states(lessons) == [["done", "done"], ["done", "open"], ["locked"]]
    assert units == [Progress(2, 2, "done"), Progress(1, 2, "open"), Progress(0, 1, "locked")]


def test_placement_unlocks_earlier_units():
    lessons, units = derive_path_progress([[False], [False], [False]], start_unit=2)
    assert states(lessons) == [["open"], ["open"], ["open"]]
    assert [u.state for u in units] == ["open", "open", "open"]


def test_empty_unit_and_path():
    assert derive_path_progress([]) == ([], [])
    _, units = derive_path_progress([[]])
    assert units == [Progress(0, 0, "open")]


def test_pick_locale():
    assert pick_locale(None) == "uz-Latn"
    assert pick_locale("ru-RU,ru;q=0.9") == "ru"
    assert pick_locale("uz-Cyrl") == "uz-Cyrl"
    assert pick_locale("fr, en;q=0.5") == "en"
