"""Campus facets of a lyceum profile: map, buildings with floor plans, specializations, offerings. Pure."""

from collections.abc import Mapping, Sequence
from typing import Any

from app.modules.lyceums.domain.rep import MAX_BODY, validate_description
from app.shared.errors import ValidationFailed

MAX_BUILDINGS = 20
MAX_PLANS_PER_BUILDING = 20
MAX_SPECIALIZATIONS = 50
MAX_SUBJECTS = 20
MAX_OFFERINGS = 50
_NAME_MAX = 200


def _names(raw: object, *, required: bool, code: str, limit: int = _NAME_MAX) -> dict[str, str]:
    cleaned = validate_description(dict(raw or {})) if isinstance(raw, Mapping) else {}
    if any(len(v) > limit for v in cleaned.values()):
        raise ValidationFailed("name too long", code=code)
    if required and not cleaned:
        raise ValidationFailed("a localized name is required", code=code)
    return cleaned


def _text(raw: object, *, limit: int, code: str) -> str | None:
    value = (str(raw) if raw is not None else "").strip()
    if len(value) > limit:
        raise ValidationFailed("value too long", code=code)
    return value or None


def _http(raw: object, code: str) -> str | None:
    value = _text(raw, limit=1000, code=code)
    if value is not None and not value.startswith(("https://", "http://")):
        raise ValidationFailed("url must be http(s)", code=code)
    return value


def _coord(raw: object, *, lo: float, hi: float, code: str) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise ValidationFailed("invalid coordinate", code=code) from e
    if not lo <= value <= hi:
        raise ValidationFailed("coordinate out of range", code=code)
    return value


def clean_map(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map block; {} when nothing is set. lat/lng must come together."""
    raw = raw or {}
    lat = _coord(raw.get("lat"), lo=-90, hi=90, code="invalid_map")
    lng = _coord(raw.get("lng"), lo=-180, hi=180, code="invalid_map")
    if (lat is None) != (lng is None):
        raise ValidationFailed("lat and lng go together", code="invalid_map")
    out: dict[str, Any] = {}
    if lat is not None and lng is not None:
        out["lat"], out["lng"] = lat, lng
    embed = _http(raw.get("embed_url"), "invalid_map")
    if embed:
        out["embed_url"] = embed
    image = _text(raw.get("image_url"), limit=500, code="invalid_map")
    if image:
        out["image_url"] = image
    return out


def clean_buildings(raw: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if len(raw) > MAX_BUILDINGS:
        raise ValidationFailed("too many buildings", code="too_many_buildings")
    out: list[dict[str, Any]] = []
    for b in raw:
        plans: list[dict[str, Any]] = []
        for p in b.get("floor_plans") or []:
            image = _text(p.get("image_url"), limit=500, code="invalid_floor_plan")
            if image is None:
                raise ValidationFailed("floor plan needs an image", code="invalid_floor_plan")
            plans.append(
                {
                    "label": _names(p.get("label"), required=False, code="invalid_floor_plan"),
                    "image_url": image,
                }
            )
        if len(plans) > MAX_PLANS_PER_BUILDING:
            raise ValidationFailed("too many floor plans", code="too_many_floor_plans")
        out.append(
            {
                "name": _names(b.get("name"), required=True, code="invalid_building"),
                "floor_plans": plans,
            }
        )
    return out


def clean_specializations(raw: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each specialization hangs off a field (direction) code, e.g. 'Aniq fanlar-3'."""
    if len(raw) > MAX_SPECIALIZATIONS:
        raise ValidationFailed("too many specializations", code="too_many_specializations")
    out: list[dict[str, Any]] = []
    for s in raw:
        field_code = _text(s.get("field_code"), limit=50, code="invalid_specialization")
        if field_code is None:
            raise ValidationFailed("field code is required", code="invalid_specialization")
        subjects = [
            _names(x, required=True, code="invalid_specialization")
            for x in (s.get("second_year_subjects") or [])
        ]
        if len(subjects) > MAX_SUBJECTS:
            raise ValidationFailed("too many subjects", code="invalid_specialization")
        out.append(
            {
                "field_code": field_code,
                "name": _names(s.get("name"), required=True, code="invalid_specialization"),
                "description": _names(
                    s.get("description"),
                    required=False,
                    code="invalid_specialization",
                    limit=MAX_BODY,
                ),
                "second_year_subjects": subjects,
            }
        )
    return out


def clean_offerings(raw: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if len(raw) > MAX_OFFERINGS:
        raise ValidationFailed("too many offerings", code="too_many_offerings")
    return [
        {
            "title": _names(o.get("title"), required=True, code="invalid_offering"),
            "description": _names(
                o.get("description"), required=False, code="invalid_offering", limit=MAX_BODY
            ),
            "taught_by": _names(
                o.get("taught_by"), required=False, code="invalid_offering", limit=MAX_BODY
            ),
        }
        for o in raw
    ]
