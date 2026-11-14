"""Invoice business logic: CRUD, status transitions, overdue. All queries are scoped by user_id."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.errors import AppError
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceItem
from app.models.user import User
from app.schemas.common import ErrorField
from app.schemas.invoice import (
    InvoiceClientOut,
    InvoiceIn,
    InvoiceItemOut,
    InvoiceListItemOut,
    InvoiceOut,
    StatusFilter,
)
from app.services import client_service
from app.services.common import not_found
from app.services.invoice_calc import AmountOutOfRangeError, LineInput, calculate_totals
from app.services.numbering import next_invoice_number

DEFAULT_PAYMENT_DAYS = 30


def today_utc() -> date:
    """Today's date in UTC (used for defaults and the overdue rule)."""
    return datetime.now(UTC).date()


def is_overdue(status: str, due_date: date, today: date) -> bool:
    """
    Overdue is computed, never stored: a sent invoice past its due date.

    Args:
        status: Stored invoice status.
        due_date: Invoice due date.
        today: Reference date.

    Returns:
        True if the invoice is sent and due_date is before today.
    """
    return status == "sent" and due_date < today


# --- Reads -------------------------------------------------------------------------------------


def get_invoice(db: Session, user_id: int, invoice_id: int, *, for_update: bool = False) -> Invoice:
    """
    Fetch one of the user's invoices with its items and client.

    Raises:
        AppError: 404 if it does not exist or belongs to another user.
    """
    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.user_id == user_id)
        .options(selectinload(Invoice.items), selectinload(Invoice.client))
        .execution_options(populate_existing=True)
    )
    if for_update:
        stmt = stmt.with_for_update(of=Invoice)
    invoice = db.scalar(stmt)
    if invoice is None:
        raise not_found("Invoice")
    return invoice


def _apply_status_filter(
    stmt: Select[Invoice, str], status: StatusFilter, today: date
) -> Select[Invoice, str]:
    if status == "overdue":
        return stmt.where(Invoice.status == "sent", Invoice.due_date < today)
    return stmt.where(Invoice.status == status)


def list_invoices(
    db: Session,
    user_id: int,
    *,
    status: StatusFilter | None = None,
    client_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    order: Literal["issue_date", "created_at"] = "issue_date",
) -> tuple[list[InvoiceListItemOut], int]:
    """
    List the user's invoices, newest first.

    Args:
        db: Database session
        user_id: Owner of the invoices
        status: Stored status, or "overdue" (sent and past due)
        client_id: Only invoices for this client
        page: 1-based page number
        page_size: Items per page
        order: Sort by issue date (default) or creation time, newest first

    Returns:
        (list rows, total matching invoices)
    """
    today = today_utc()
    stmt: Select[Invoice, str] = (
        select(Invoice, Client.name)
        .join(Client, (Client.id == Invoice.client_id) & (Client.user_id == Invoice.user_id))
        .where(Invoice.user_id == user_id)
    )
    if status is not None:
        stmt = _apply_status_filter(stmt, status, today)
    if client_id is not None:
        stmt = stmt.where(Invoice.client_id == client_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    sort_column = Invoice.issue_date if order == "issue_date" else Invoice.created_at
    rows = db.execute(
        stmt.order_by(sort_column.desc(), Invoice.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [to_list_item(invoice, client_name, today) for invoice, client_name in rows], total


# --- Writes ------------------------------------------------------------------------------------


def _ensure_draft(invoice: Invoice) -> None:
    if invoice.status != "draft":
        raise AppError(
            409,
            "invoice_not_editable",
            f"Only draft invoices can be changed; this invoice is {invoice.status}.",
        )


def _apply_input(db: Session, user: User, invoice: Invoice, data: InvoiceIn) -> None:
    """Validate references and dates, compute totals and write fields + items onto `invoice`."""
    client_service.get_client(db, user.id, data.client_id)  # 404 for unknown/foreign clients

    issue_date = data.issue_date or today_utc()
    due_date = data.due_date or issue_date + timedelta(days=DEFAULT_PAYMENT_DAYS)
    if due_date < issue_date:
        raise AppError(
            422,
            "validation_error",
            "The due date must be on or after the issue date.",
            [ErrorField(field="dueDate", message="must be on or after the issue date")],
        )

    tax_rate = data.tax_rate if data.tax_rate is not None else user.default_tax_rate
    try:
        totals = calculate_totals(
            [LineInput(item.quantity, item.unit_price) for item in data.items], tax_rate
        )
    except AmountOutOfRangeError as exc:
        raise AppError(422, "amount_out_of_range", str(exc)) from exc

    invoice.client_id = data.client_id
    invoice.issue_date = issue_date
    invoice.due_date = due_date
    invoice.currency = data.currency or user.default_currency
    invoice.tax_rate = tax_rate
    invoice.subtotal = totals.subtotal
    invoice.tax_amount = totals.tax_amount
    invoice.total = totals.total
    invoice.notes = data.notes

    if invoice.items:
        invoice.items.clear()
        db.flush()  # delete old rows before re-using their positions
    invoice.items.extend(
        InvoiceItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=amount,
            position=position,
        )
        for position, (item, amount) in enumerate(zip(data.items, totals.line_amounts, strict=True))
    )


def create_invoice(db: Session, user: User, data: InvoiceIn) -> Invoice:
    """
    Create a draft invoice with a new sequential number.

    Args:
        db: Database session
        user: Owner of the invoice
        data: Invoice fields and line items

    Returns:
        The created invoice with items and client loaded.
    """
    invoice = Invoice(user_id=user.id, status="draft")
    _apply_input(db, user, invoice, data)
    invoice.invoice_number = next_invoice_number(db, user.id)
    db.add(invoice)
    db.commit()
    return get_invoice(db, user.id, invoice.id)


def update_invoice(db: Session, user: User, invoice_id: int, data: InvoiceIn) -> Invoice:
    """
    Replace a draft invoice's fields and items (the number never changes).

    Raises:
        AppError: 409 if the invoice is not a draft.
    """
    invoice = get_invoice(db, user.id, invoice_id, for_update=True)
    _ensure_draft(invoice)
    _apply_input(db, user, invoice, data)
    db.commit()
    return get_invoice(db, user.id, invoice.id)


def delete_invoice(db: Session, user_id: int, invoice_id: int) -> None:
    """
    Delete a draft invoice. Its number is not reused.

    Raises:
        AppError: 409 if the invoice is not a draft (void it instead).
    """
    invoice = get_invoice(db, user_id, invoice_id, for_update=True)
    _ensure_draft(invoice)
    db.delete(invoice)
    db.commit()


def _transition(
    db: Session,
    user_id: int,
    invoice_id: int,
    allowed_from: tuple[str, ...],
    action: str,
) -> Invoice:
    invoice = get_invoice(db, user_id, invoice_id, for_update=True)
    if invoice.status not in allowed_from:
        raise AppError(
            409,
            "invalid_status_transition",
            f"Cannot {action} an invoice that is {invoice.status}.",
        )
    return invoice


def send_invoice(db: Session, user_id: int, invoice_id: int) -> Invoice:
    """Mark a draft as sent (no email is sent in the MVP). draft -> sent."""
    invoice = _transition(db, user_id, invoice_id, ("draft",), "send")
    invoice.status = "sent"
    invoice.sent_at = datetime.now(UTC)
    db.commit()
    return get_invoice(db, user_id, invoice_id)


def mark_invoice_paid(db: Session, user_id: int, invoice_id: int) -> Invoice:
    """Record full payment. sent (incl. overdue) -> paid."""
    invoice = _transition(db, user_id, invoice_id, ("sent",), "mark as paid")
    invoice.status = "paid"
    invoice.amount_paid = invoice.total
    invoice.paid_at = datetime.now(UTC)
    db.commit()
    return get_invoice(db, user_id, invoice_id)


def void_invoice(db: Session, user_id: int, invoice_id: int) -> Invoice:
    """Cancel an unpaid invoice. draft or sent -> void."""
    invoice = _transition(db, user_id, invoice_id, ("draft", "sent"), "void")
    invoice.status = "void"
    db.commit()
    return get_invoice(db, user_id, invoice_id)


# --- Serialization -----------------------------------------------------------------------------


def to_invoice_out(invoice: Invoice, today: date | None = None) -> InvoiceOut:
    """Build the API representation of an invoice (adds isOverdue and balanceDue)."""
    ref = today or today_utc()
    return InvoiceOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        client_id=invoice.client_id,
        client=InvoiceClientOut.model_validate(invoice.client),
        status=invoice.status,  # type: ignore[arg-type]  # DB CHECK guarantees a valid status
        is_overdue=is_overdue(invoice.status, invoice.due_date, ref),
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        currency=invoice.currency,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total=invoice.total,
        amount_paid=invoice.amount_paid,
        balance_due=invoice.total - invoice.amount_paid,
        notes=invoice.notes,
        sent_at=invoice.sent_at,
        paid_at=invoice.paid_at,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        items=[InvoiceItemOut.model_validate(item) for item in invoice.items],
    )


def to_list_item(invoice: Invoice, client_name: str, today: date) -> InvoiceListItemOut:
    """Build a list row for an invoice."""
    return InvoiceListItemOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        client_id=invoice.client_id,
        client_name=client_name,
        status=invoice.status,  # type: ignore[arg-type]  # DB CHECK guarantees a valid status
        is_overdue=is_overdue(invoice.status, invoice.due_date, today),
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        currency=invoice.currency,
        total=invoice.total,
        amount_paid=invoice.amount_paid,
        balance_due=invoice.total - invoice.amount_paid,
    )
