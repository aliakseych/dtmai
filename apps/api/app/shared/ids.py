import uuid

import uuid_utils


def new_id() -> uuid.UUID:
    """Time-ordered UUIDv7 as a stdlib UUID."""
    return uuid.UUID(str(uuid_utils.uuid7()))
