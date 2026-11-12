import pytest

from app.modules.lyceums.domain.campus import (
    clean_buildings,
    clean_map,
    clean_offerings,
    clean_specializations,
)
from app.shared.errors import ValidationFailed


def test_map_empty_and_coords():
    assert clean_map(None) == {}
    assert clean_map({"lat": "41.3", "lng": 69.2, "embed_url": ""}) == {"lat": 41.3, "lng": 69.2}


@pytest.mark.parametrize(
    "raw",
    [{"lat": 41.3}, {"lat": 91, "lng": 0}, {"embed_url": "javascript:x"}],
)
def test_map_rejects_bad(raw):
    with pytest.raises(ValidationFailed) as e:
        clean_map(raw)
    assert e.value.code == "invalid_map"


def test_buildings_floor_plans():
    out = clean_buildings(
        [
            {
                "name": {"en": " Main "},
                "floor_plans": [{"label": {"en": "1"}, "image_url": "media/a.png"}],
            }
        ]
    )
    assert out == [
        {
            "name": {"en": "Main"},
            "floor_plans": [{"label": {"en": "1"}, "image_url": "media/a.png"}],
        }
    ]
    with pytest.raises(ValidationFailed):
        clean_buildings([{"name": {}}])
    with pytest.raises(ValidationFailed):
        clean_buildings([{"name": {"en": "A"}, "floor_plans": [{"image_url": " "}]}])


def test_specializations_need_field_and_name():
    out = clean_specializations(
        [
            {
                "field_code": "Aniq fanlar-3",
                "name": {"uz-Latn": "Texnik-dasturchi"},
                "second_year_subjects": [{"en": "C++"}],
            }
        ]
    )
    assert out[0]["second_year_subjects"] == [{"en": "C++"}]
    assert out[0]["description"] == {}
    with pytest.raises(ValidationFailed):
        clean_specializations([{"field_code": "", "name": {"en": "x"}}])
    with pytest.raises(ValidationFailed):
        clean_specializations([{"field_code": "A", "name": {"de": "x"}}])


def test_offerings_title_required():
    out = clean_offerings(
        [{"title": {"en": "SAT prep"}, "taught_by": {"en": "University students"}}]
    )
    assert out[0]["taught_by"] == {"en": "University students"}
    with pytest.raises(ValidationFailed):
        clean_offerings([{"title": {}}])
