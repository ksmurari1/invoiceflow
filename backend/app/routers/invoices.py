"""Invoice endpoints: /api/v1/invoices."""

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import ErrorResponse, Page
from app.schemas.invoice import InvoiceIn, InvoiceListItemOut, InvoiceOut, StatusFilter
from app.services import invoice_service
from app.services.pdf import pdf_filename, render_invoice_pdf

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)

_CONFLICT: dict[int | str, dict[str, Any]] = {409: {"model": ErrorResponse}}


@router.get("", response_model=Page[InvoiceListItemOut])
async def list_invoices(
    status: StatusFilter | None = Query(default=None),
    client_id: int | None = Query(default=None, alias="clientId", ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[InvoiceListItemOut]:
    """List invoices, newest first. `status=overdue` returns sent invoices past their due date."""
    items, total = invoice_service.list_invoices(
        db, user.id, status=status, client_id=client_id, page=page, page_size=page_size
    )
    return Page[InvoiceListItemOut](items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    data: InvoiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Create a draft invoice. Totals and the invoice number are assigned by the server."""
    return invoice_service.to_invoice_out(invoice_service.create_invoice(db, user, data))


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def read_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Get an invoice with its items."""
    return invoice_service.to_invoice_out(invoice_service.get_invoice(db, user.id, invoice_id))


@router.put("/{invoice_id}", response_model=InvoiceOut, responses=_CONFLICT)
async def update_invoice(
    invoice_id: int,
    data: InvoiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Replace a draft invoice and its items (409 if not a draft)."""
    return invoice_service.to_invoice_out(
        invoice_service.update_invoice(db, user, invoice_id, data)
    )


@router.delete("/{invoice_id}", status_code=204, response_class=Response, responses=_CONFLICT)
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Delete a draft invoice (409 if not a draft — void it instead)."""
    invoice_service.delete_invoice(db, user.id, invoice_id)
    return Response(status_code=204)


@router.post("/{invoice_id}/send", response_model=InvoiceOut, responses=_CONFLICT)
async def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Mark a draft as sent (draft -> sent). No email is sent in the MVP."""
    return invoice_service.to_invoice_out(invoice_service.send_invoice(db, user.id, invoice_id))


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut, responses=_CONFLICT)
async def mark_invoice_paid(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Mark a sent invoice as fully paid (sent -> paid)."""
    return invoice_service.to_invoice_out(
        invoice_service.mark_invoice_paid(db, user.id, invoice_id)
    )


@router.post("/{invoice_id}/void", response_model=InvoiceOut, responses=_CONFLICT)
async def void_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    """Void an unpaid invoice (draft or sent -> void)."""
    return invoice_service.to_invoice_out(invoice_service.void_invoice(db, user.id, invoice_id))


@router.get(
    "/{invoice_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "Invoice PDF"}},
)
async def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Download the invoice as a PDF."""
    invoice = invoice_service.get_invoice(db, user.id, invoice_id)
    overdue = invoice_service.is_overdue(
        invoice.status, invoice.due_date, invoice_service.today_utc()
    )
    content = await run_in_threadpool(render_invoice_pdf, invoice, user, is_overdue=overdue)
    filename = pdf_filename(invoice.invoice_number)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
