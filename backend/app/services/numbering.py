"""Sequential, per-user invoice numbers (INV-0001, INV-0002, ...)."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.invoice import InvoiceCounter

DEFAULT_PREFIX = "INV-"


def next_invoice_number(db: Session, user_id: int, prefix: str = DEFAULT_PREFIX) -> str:
    """
    Reserve the user's next invoice number inside the caller's transaction.

    The counter row is created if missing, then locked with SELECT ... FOR UPDATE, so
    concurrent requests for the same user are serialized and never get the same number.
    The number is only consumed if the caller commits; numbers are never reused.

    Args:
        db: Database session (the caller commits).
        user_id: Owner of the invoice.
        prefix: Number prefix.

    Returns:
        The formatted number, e.g. "INV-0001".
    """
    db.execute(
        insert(InvoiceCounter)
        .values(user_id=user_id, next_number=1)
        .on_conflict_do_nothing(index_elements=[InvoiceCounter.user_id])
    )
    counter = db.scalars(
        select(InvoiceCounter)
        .where(InvoiceCounter.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).one()
    number = counter.next_number
    counter.next_number = number + 1
    db.flush()
    return f"{prefix}{number:04d}"
