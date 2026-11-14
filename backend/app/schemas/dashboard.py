"""Dashboard schemas."""

from app.schemas.common import CamelModel, Money
from app.schemas.invoice import InvoiceListItemOut


class Bucket(CamelModel):
    """Number of invoices and their amount."""

    count: int
    amount: Money


class CurrencySummary(CamelModel):
    """
    Totals for one currency (amounts in different currencies are never added together).

    - draft: draft invoices, amount = total
    - outstanding: sent invoices (including overdue), amount = balance due
    - overdue: sent invoices past their due date, amount = balance due
    - paid: paid invoices, amount = total
    """

    currency: str
    draft: Bucket
    outstanding: Bucket
    overdue: Bucket
    paid: Bucket


class DashboardSummary(CamelModel):
    """Overview of the user's invoicing."""

    client_count: int
    invoice_count: int
    currencies: list[CurrencySummary]
    recent_invoices: list[InvoiceListItemOut]
