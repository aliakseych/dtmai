import pytest

from app.modules.identity.domain.models import normalize_email, validate_password
from app.modules.identity.infrastructure.passwords import Argon2Hasher
from app.shared.errors import ValidationFailed


def test_hash_and_verify() -> None:
    h = Argon2Hasher()
    hashed = h.hash("correct horse")
    assert hashed != "correct horse"
    assert h.verify("correct horse", hashed)
    assert not h.verify("wrong", hashed)
    assert not h.verify("x", "not-a-hash")


def test_salted() -> None:
    h = Argon2Hasher()
    assert h.hash("same-password") != h.hash("same-password")


def test_password_policy() -> None:
    with pytest.raises(ValidationFailed):
        validate_password("short")
    assert validate_password("long-enough-1")


def test_email_normalized() -> None:
    assert normalize_email("  Ali@Example.UZ ") == "ali@example.uz"
    with pytest.raises(ValidationFailed):
        normalize_email("nope")
