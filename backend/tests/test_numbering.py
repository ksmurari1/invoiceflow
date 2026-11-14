"""Sequential per-user invoice numbers."""

import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.numbering import next_invoice_number
from tests.factories import make_user


def test_numbers_are_sequential_per_user(db_session: Session, demo_user: User) -> None:
    other = make_user(db_session)

    assert next_invoice_number(db_session, demo_user.id) == "INV-0001"
    assert next_invoice_number(db_session, demo_user.id) == "INV-0002"
    assert next_invoice_number(db_session, other.id) == "INV-0001"
    assert next_invoice_number(db_session, demo_user.id) == "INV-0003"


def test_number_width_grows_past_9999(db_session: Session, demo_user: User) -> None:
    from app.models.invoice import InvoiceCounter

    db_session.add(InvoiceCounter(user_id=demo_user.id, next_number=10000))
    db_session.flush()

    assert next_invoice_number(db_session, demo_user.id) == "INV-10000"


def test_concurrent_requests_get_unique_consecutive_numbers(engine: Engine) -> None:
    """Real committed transactions in parallel threads (not the rollback fixture)."""
    with Session(engine) as setup:
        user = User(email=f"concurrency-{uuid.uuid4().hex[:8]}@example.com")
        setup.add(user)
        setup.commit()
        user_id = user.id

    def reserve() -> str:
        with Session(engine) as session:
            number = next_invoice_number(session, user_id)
            session.commit()
            return number

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            numbers = list(pool.map(lambda _: reserve(), range(20)))
    finally:
        with Session(engine) as cleanup:
            cleanup.execute(delete(User).where(User.id == user_id))
            cleanup.commit()

    assert sorted(numbers) == [f"INV-{n:04d}" for n in range(1, 21)]
