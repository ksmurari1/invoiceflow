"""Invoice request/response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, field_validator

from app.schemas.common import CamelModel, Money, Quantity, Rate, RequestModel

Currency = Literal["USD", "EUR", "GBP", "CAD", "AUD", "INR"]
InvoiceStatus = Literal["draft", "sent", "paid", "void"]
StatusFilter = Literal["draft", "sent", "paid", "void", "overdue"]

LineQuantity = Annotated[Quantity, Field(gt=0, le=Decimal("1000000"))]
UnitPrice = Annotated[Money, Field(ge=0, le=Decimal("9999999.99"))]
TaxRate = Annotated[Rate, Field(ge=0, le=100)]


class InvoiceItemIn(RequestModel):
    """One line item. Its amount is always computed by the server."""

    description: str = Field(min_length=1, max_length=500)
    quantity: LineQuantity
    unit_price: UnitPrice

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> object:
        """Trim surrounding whitespace."""
        return value.strip() if isinstance(value, str) else value


class InvoiceIn(RequestModel):
    """
    Create a draft invoice or fully replace a draft.

    Omitted values default to: issueDate = today, dueDate = issueDate + 30 days,
    currency and taxRate = the user's defaults. Totals are never accepted from clients.
    """

    client_id: int = Field(gt=0)
    issue_date: date | None = None
    due_date: date | None = None
    currency: Currency | None = None
    tax_rate: TaxRate | None = None
    notes: str | None = Field(default=None, max_length=5000)
    items: list[InvoiceItemIn] = Field(min_length=1, max_length=100)

    @field_validator("notes", mode="before")
    @classmethod
    def blank_notes_to_none(cls, value: object) -> object:
        """Store empty notes as null."""
        if isinstance(value, str):
            return value.strip() or None
        return value


class InvoiceItemOut(CamelModel):
    """A stored line item."""

    id: int
    description: str
    quantity: Quantity
    unit_price: Money
    amount: Money
    position: int


class InvoiceClientOut(CamelModel):
    """Client details embedded in an invoice."""

    id: int
    name: str
    email: str
    company: str | None
    address: str | None


class InvoiceOut(CamelModel):
    """Full invoice with items and computed fields."""

    id: int
    invoice_number: str
    client_id: int
    client: InvoiceClientOut
    status: InvoiceStatus
    is_overdue: bool
    issue_date: date
    due_date: date
    currency: str
    subtotal: Money
    tax_rate: Rate
    tax_amount: Money
    total: Money
    amount_paid: Money
    balance_due: Money
    notes: str | None
    sent_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceItemOut]


class InvoiceListItemOut(CamelModel):
    """Invoice row for lists."""

    id: int
    invoice_number: str
    client_id: int
    client_name: str
    status: InvoiceStatus
    is_overdue: bool
    issue_date: date
    due_date: date
    currency: str
    total: Money
    amount_paid: Money
    balance_due: Money
