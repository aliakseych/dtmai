from app.modules.lyceums.domain.campus import clean_offerings, clean_specializations


def test_long_descriptions_accepted() -> None:
    text = "x" * 1200
    off = clean_offerings(
        [{"title": {"en": "Club"}, "description": {"en": text}, "taught_by": {"en": text}}]
    )
    assert len(off[0]["description"]["en"]) == 1200
    spec = clean_specializations(
        [{"field_code": "A1", "name": {"en": "Math"}, "description": {"en": text}}]
    )
    assert len(spec[0]["description"]["en"]) == 1200
