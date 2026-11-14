"""Invoice, its line items, and the per-user invoice number counter."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.client import Client
from app.models.mixins import TimestampMixin

INVOICE_STATUSES = ("draft", "sent", "paid", "void")


class Invoice(TimestampMixin, Base):
    """An invoice owned by a user and billed to one of that user's clients."""

    __tablename__ = "invoices"
    __table_args__ = (
        # Composite FK: the client must belong to the same user as the invoice.
        ForeignKeyConstraint(["client_id", "user_id"], ["clients.id", "clients.user_id"]),
        UniqueConstraint("user_id", "invoice_number"),
        CheckConstraint("status IN ('draft', 'sent', 'paid', 'void')", name="status_valid"),
        CheckConstraint("due_date >= issue_date", name="due_on_or_after_issue"),
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="tax_rate_range"),
        CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 AND total >= 0", name="amounts_non_negative"
        ),
        CheckConstraint("amount_paid >= 0 AND amount_paid <= total", name="amount_paid_range"),
        Index("ix_invoices_user_id_status", "user_id", "status"),
        Index("ix_invoices_user_id_due_date", "user_id", "due_date"),
        Index("ix_invoices_user_id_issue_date", "user_id", "issue_date"),
        Index("ix_invoices_client_id", "client_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    client_id: Mapped[int]
    invoice_number: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10), server_default="draft")
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.position",
        passive_deletes=True,
    )
    client: Mapped[Client] = relationship(viewonly=True)


class InvoiceItem(Base):
    """A line on an invoice. `amount` is computed server-side (quantity x unit_price)."""

    __tablename__ = "invoice_items"
    __table_args__ = (
        UniqueConstraint("invoice_id", "position"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    position: Mapped[int]

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class InvoiceCounter(Base):
    """Next sequential invoice number per user. Locked with SELECT ... FOR UPDATE when used."""

    __tablename__ = "invoice_counters"
    __table_args__ = (CheckConstraint("next_number >= 1", name="next_number_positive"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    next_number: Mapped[int] = mapped_column(server_default="1")
