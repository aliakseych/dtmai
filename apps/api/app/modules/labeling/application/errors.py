from app.shared.errors import Conflict, DomainError, NotFound, ValidationFailed

__all__ = [
    "AuditAgreementLow",
    "NothingToReview",
    "QueueItemGone",
    "UndoNotAllowed",
    "Conflict",
    "NotFound",
    "ValidationFailed",
    "DomainError",
]


class NothingToReview(DomainError):
    status = 404
    code = "queue_empty"


class QueueItemGone(Conflict):
    code = "queue_item_resolved"


class UndoNotAllowed(Conflict):
    code = "undo_not_allowed"


class AuditAgreementLow(Conflict):
    code = "audit_agreement_low"
