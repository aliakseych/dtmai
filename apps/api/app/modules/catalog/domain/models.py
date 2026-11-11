"""Pure catalog rules: validation/normalisation of admin-entered data and tree helpers.

Entities are plain dicts at the boundary (the admin CRUD is generic over entities); every
`validate_*` returns a cleaned dict or raises `Invalid`.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any
from uuid import UUID

from app.shared.question_kinds import QUESTION_KINDS

LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
BLUEPRINT_KINDS = ("official", "generated", "template")
SOURCE_KINDS = ("previous_year", "bluebook", "ai_generated", "harvested", "custom")
LABEL_SCHEMES = ("latin", "cyrillic", "numeric", "none")

_LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
_CODE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")


class Invalid(ValueError):
    """Admin input violates a catalog rule."""


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise Invalid(msg)


def validate_names(names: Any, *, field: str = "names") -> dict[str, str]:
    _need(isinstance(names, Mapping) and len(names) > 0, f"{field} must be a non-empty object")
    out: dict[str, str] = {}
    for k, v in names.items():
        _need(k in LOCALES, f"{field}: unknown locale {k!r}")
        _need(isinstance(v, str), f"{field}.{k} must be a string")
        if v.strip():
            out[k] = v.strip()
    _need(bool(out), f"{field} needs at least one non-empty value")
    return out


def pick_name(names: Mapping[str, str], locale: str = "uz-Latn") -> str:
    for k in (locale, "uz-Latn", "ru", "en", "uz-Cyrl"):
        if names.get(k):
            return names[k]
    return next(iter(names.values()), "")


def validate_code(code: Any) -> str:
    _need(isinstance(code, str) and bool(_CODE.match(code)), "code must match [a-z0-9][a-z0-9_-]{0,63}")
    return code


def validate_language(lang: Any) -> str:
    _need(isinstance(lang, str) and bool(_LANG.match(lang)), "invalid content language code")
    return lang


def uuid_list(raw: Any, field: str) -> list[str]:
    _need(isinstance(raw, list | tuple), f"{field} must be a list")
    out: list[str] = []
    for v in raw:
        try:
            out.append(str(UUID(str(v))))
        except ValueError as e:
            raise Invalid(f"{field}: {v!r} is not a uuid") from e
    return list(dict.fromkeys(out))


def validate_type_config(kind: str, config: Any) -> dict[str, Any]:
    """QuestionType.config: option_count, label_scheme, image_stem, option_style, rules."""
    _need(kind in QUESTION_KINDS, f"unknown kind {kind!r}")
    _need(isinstance(config, Mapping), "config must be an object")
    cfg = dict(config)
    if "option_count" in cfg:
        oc = cfg["option_count"]
        _need(isinstance(oc, int) and not isinstance(oc, bool) and 2 <= oc <= 10, "option_count must be 2..10")
        _need(kind in ("single_choice", "multi_choice"), "option_count only applies to choice kinds")
    if "label_scheme" in cfg:
        _need(cfg["label_scheme"] in LABEL_SCHEMES, f"label_scheme must be one of {LABEL_SCHEMES}")
    if "image_stem" in cfg:
        _need(isinstance(cfg["image_stem"], bool), "image_stem must be a boolean")
    if "rules" in cfg:
        _need(isinstance(cfg["rules"], list) and all(isinstance(r, str) for r in cfg["rules"]), "rules must be a list of strings")
    return cfg


def validate_lesson_selectors(data: Mapping[str, Any]) -> dict[str, Any]:
    qc = data.get("question_count", 10)
    _need(isinstance(qc, int) and not isinstance(qc, bool) and 1 <= qc <= 100, "question_count must be 1..100")
    return {
        "topic_ids": uuid_list(data.get("topic_ids", []), "topic_ids"),
        "type_ids": uuid_list(data.get("type_ids", []), "type_ids"),
        "question_count": qc,
        "legendary": bool(data.get("legendary", False)),
    }


def validate_blueprint_sections(sections: Any) -> list[dict[str, Any]]:
    _need(isinstance(sections, list) and len(sections) > 0, "sections must be a non-empty list")
    out: list[dict[str, Any]] = []
    for i, s in enumerate(sections):
        _need(isinstance(s, Mapping), f"sections[{i}] must be an object")
        subj = uuid_list([s.get("subject_id")], f"sections[{i}].subject_id")[0]
        count, weight = s.get("count"), s.get("weight", 1.0)
        _need(isinstance(count, int) and not isinstance(count, bool) and count > 0, f"sections[{i}].count must be > 0")
        _need(isinstance(weight, int | float) and not isinstance(weight, bool) and weight >= 0, f"sections[{i}].weight must be >= 0")
        sec: dict[str, Any] = {
            "subject_id": subj,
            "topic_ids": uuid_list(s.get("topic_ids", []), f"sections[{i}].topic_ids"),
            "type_ids": uuid_list(s.get("type_ids", []), f"sections[{i}].type_ids"),
            "count": count,
            "weight": float(weight),
        }
        if s.get("question_ids"):  # fixed paper (official mocks)
            qids = uuid_list(s["question_ids"], f"sections[{i}].question_ids")
            _need(len(qids) == count, f"sections[{i}].question_ids must contain exactly count ids")
            sec["question_ids"] = qids
        out.append(sec)
    return out


def descendants(parent_of: Mapping[str, str | None], roots: Iterable[str]) -> list[str]:
    """Roots plus all their descendants in a topic tree given as {id: parent_id}."""
    children: dict[str, list[str]] = {}
    for cid, pid in parent_of.items():
        if pid:
            children.setdefault(pid, []).append(cid)
    seen: dict[str, None] = {}
    stack = list(roots)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen[n] = None
        stack.extend(children.get(n, []))
    return list(seen)


def creates_cycle(parent_of: Mapping[str, str | None], node: str, new_parent: str | None) -> bool:
    cur = new_parent
    while cur is not None:
        if cur == node:
            return True
        cur = parent_of.get(cur)
    return False


def lesson_visible(pool: int, question_count: int, min_pool: int) -> bool:
    return pool >= max(min_pool, question_count)


def validate_entity(entity: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalise a full entity dict (create or merged update)."""
    d = dict(data)
    match entity:
        case "subject":
            d["code"] = validate_code(d.get("code"))
            d["names"] = validate_names(d.get("names"))
            w = d.get("weight", 1.0)
            _need(isinstance(w, int | float) and not isinstance(w, bool) and w >= 0, "weight must be >= 0")
            d["weight"] = float(w)
        case "topic":
            d["names"] = validate_names(d.get("names"))
            if d.get("code"):
                d["code"] = validate_code(d["code"])
        case "question_type":
            d["code"] = validate_code(d.get("code"))
            d["names"] = validate_names(d.get("names"))
            d["config"] = validate_type_config(d.get("kind", ""), d.get("config", {}))
            _need(isinstance(d.get("rules", {}), Mapping), "rules must be an object")
            _need(isinstance(d.get("generation_prompt", ""), str), "generation_prompt must be a string")
        case "path":
            d["language"] = validate_language(d.get("language"))
            d["names"] = validate_names(d.get("names"))
        case "unit":
            d["names"] = validate_names(d.get("names"))
        case "lesson":
            d["names"] = validate_names(d.get("names"))
            d.update(validate_lesson_selectors(d))
        case "blueprint":
            d["code"] = validate_code(d.get("code"))
            d["names"] = validate_names(d.get("names"))
            _need(d.get("kind") in BLUEPRINT_KINDS, f"kind must be one of {BLUEPRINT_KINDS}")
            dm = d.get("duration_min")
            _need(isinstance(dm, int) and not isinstance(dm, bool) and 1 <= dm <= 600, "duration_min must be 1..600")
            d["sections"] = validate_blueprint_sections(d.get("sections"))
        case "question_base":
            d["code"] = validate_code(d.get("code"))
            d["names"] = validate_names(d.get("names"))
            _need(d.get("kind") in SOURCE_KINDS, f"kind must be one of {SOURCE_KINDS}")
            y = d.get("year")
            _need(y is None or (isinstance(y, int) and 1990 <= y <= 2100), "year must be 1990..2100")
        case _:
            raise Invalid(f"unknown entity {entity!r}")
    return d


def sequence_is_permutation(current: Sequence[Any], proposed: Sequence[Any]) -> bool:
    return len(current) == len(proposed) and set(current) == set(proposed) and len(set(proposed)) == len(proposed)
