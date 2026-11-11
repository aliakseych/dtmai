from uuid import uuid4

import pytest

from app.modules.identity.domain.models import User, validate_dream_lyceum_ids
from app.shared.errors import ValidationFailed


def test_ordered_up_to_three():
    ids = [uuid4(), uuid4(), uuid4()]
    assert validate_dream_lyceum_ids(ids) == ids
    assert validate_dream_lyceum_ids([]) == []


def test_too_many():
    with pytest.raises(ValidationFailed) as e:
        validate_dream_lyceum_ids([uuid4() for _ in range(4)])
    assert e.value.code == "too_many_dream_lyceums"


def test_duplicate():
    a = uuid4()
    with pytest.raises(ValidationFailed) as e:
        validate_dream_lyceum_ids([a, uuid4(), a])
    assert e.value.code == "duplicate_dream_lyceum"


def test_target_is_first_choice():
    a = uuid4()
    assert User(id=uuid4(), name="n", email="a@b.c", dream_lyceum_ids=[a, uuid4()]).target_lyceum_id == a
    assert User(id=uuid4(), name="n", email="a@b.c").target_lyceum_id is None
