"""Dashboard aggregates. Every query is scoped by user_id."""

from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.dashboard import Bucket, CurrencySummary, DashboardSummary
from app.services.invoice_service import list_invoices, today_utc

RECENT_LIMIT = 5


@dataclass
class _Acc:
    count: int = 0
    amount: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def add(self, count: int, amount: Decimal) -> None:
        self.count += count
        self.amount += amount

    def bucket(self) -> Bucket:
        return Bucket(count=self.count, amount=self.amount)


def get_summary(db: Session, user: User) -> DashboardSummary:
    """
    Build the dashboard summary for a user.

    Args:
        db: Database session
        user: Owner of the data

    Returns:
        Client/invoice counts, per-currency buckets (user's default currency first),
        and the most recently created invoices.
    """
    today = today_utc()
    past_due = (Invoice.due_date < today).label("past_due")
    rows = db.execute(
        select(
            Invoice.currency,
            Invoice.status,
            past_due,
            func.count(),
            func.coalesce(func.sum(Invoice.total), 0),
            func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0),
        )
        .where(Invoice.user_id == user.id)
        .group_by(Invoice.currency, Invoice.status, past_due)
    ).all()

    per_currency: dict[str, dict[str, _Acc]] = {}
    invoice_count = 0
    for currency, status, is_past_due, count, total, balance in rows:
        invoice_count += count
        acc = per_currency.setdefault(
            currency, {name: _Acc() for name in ("draft", "outstanding", "overdue", "paid")}
        )
        if status == "draft":
            acc["draft"].add(count, total)
        elif status == "sent":
            acc["outstanding"].add(count, balance)
            if is_past_due:
                acc["overdue"].add(count, balance)
        elif status == "paid":
            acc["paid"].add(count, total)
        # void invoices are counted in invoice_count only

    ordered = sorted(per_currency, key=lambda c: (c != user.default_currency, c))
    currencies = [
        CurrencySummary(
            currency=c,
            draft=per_currency[c]["draft"].bucket(),
            outstanding=per_currency[c]["outstanding"].bucket(),
            overdue=per_currency[c]["overdue"].bucket(),
            paid=per_currency[c]["paid"].bucket(),
        )
        for c in ordered
    ]

    client_count = (
        db.scalar(select(func.count()).select_from(Client).where(Client.user_id == user.id)) or 0
    )
    recent, _ = list_invoices(db, user.id, page=1, page_size=RECENT_LIMIT, order="created_at")

    return DashboardSummary(
        client_count=client_count,
        invoice_count=invoice_count,
        currencies=currencies,
        recent_invoices=recent,
    )
