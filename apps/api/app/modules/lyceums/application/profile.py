from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.modules.lyceums.domain.profile import (
    CityView,
    normalize_city_code,
    parse_dormitory_status,
    validate_dormitory_description,
)
from app.modules.lyceums.domain.rep import (
    MAX_COURSES,
    MAX_GALLERY,
    validate_contacts,
    validate_description,
    validate_string_list,
)
from app.modules.lyceums.ports import CityRepository, LyceumProfiles
from app.shared.errors import NotFound, ValidationFailed


def _clean(value: object) -> str | None:
    return (str(value) if value is not None else "").strip() or None


class ProfileService:
    """Validates and applies profile edits; callers decide who may edit which keys."""

    def __init__(self, profiles: LyceumProfiles, cities: CityRepository) -> None:
        self._profiles, self._cities = profiles, cities

    async def cities(self, locale: str) -> list[CityView]:
        """Cities sorted by their name in `locale`."""
        return await self._cities.list_with_counts(locale)

    async def update(self, lyceum_id: UUID, raw: Mapping[str, Any]) -> list[str]:
        """Apply the sent keys (already filtered by the caller); returns the changed keys."""
        fields: dict[str, object] = {}
        for key, value in raw.items():
            if key in ("logo_url", "campus_photo_url", "university_name", "website"):
                fields[key] = _clean(value)
            elif key == "city":
                code = normalize_city_code(value)
                if code is not None and not await self._cities.exists(code):
                    raise ValidationFailed("unknown city", code="unknown_city")
                fields[key] = code
            elif key == "gallery_urls":
                fields[key] = validate_string_list(
                    value or [], limit=MAX_GALLERY, code="too_many_gallery_urls"
                )
            elif key == "courses":
                fields[key] = validate_string_list(
                    value or [], limit=MAX_COURSES, code="too_many_courses"
                )
            elif key == "description":
                fields[key] = validate_description(value or {})
            elif key == "contacts":
                fields[key] = validate_contacts(value or {})
            elif key == "dormitory_status":
                fields[key] = parse_dormitory_status(value or "").value
            elif key == "dormitory_description":
                fields[key] = validate_dormitory_description(value or {})
            elif key == "verified_rep":
                if value is not None:
                    fields[key] = bool(value)
            else:
                raise ValidationFailed(f"unknown profile field: {key}", code="invalid_field")
        if not await self._profiles.update_fields(lyceum_id, fields):
            raise NotFound("lyceum not found", code="lyceum_not_found")
        return sorted(fields)
