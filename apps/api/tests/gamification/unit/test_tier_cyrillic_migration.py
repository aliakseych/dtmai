import importlib.util
import re
from pathlib import Path

PATH = (
    Path(__file__).parents[3]
    / "migrations/versions/gamification/gamification_0004_tier_cyrillic.py"
)


def test_tier_names_are_cyrillic() -> None:
    spec = importlib.util.spec_from_file_location("g0004", PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert set(mod.TIERS_CYRL) == {"bronze", "silver", "gold", "platinum", "diamond"}
    assert all(re.fullmatch(r"[А-Яа-яЎўҚқҒғҲҳ]+", v) for v in mod.TIERS_CYRL.values())
