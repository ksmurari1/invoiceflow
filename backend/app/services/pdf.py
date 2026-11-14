"""
Invoice PDF rendering with ReportLab.

All user-supplied text is XML-escaped before it reaches a Paragraph (Paragraph parses
markup), so names like "<b>x</b>" print literally instead of being interpreted.
Money is formatted from Decimal directly — no float conversion.
"""

import io
import re
from decimal import Decimal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.invoice import Invoice
from app.models.user import User

_STYLES = getSampleStyleSheet()
_BODY = ParagraphStyle("Body", parent=_STYLES["BodyText"], fontSize=9.5, leading=13)
_SMALL = ParagraphStyle("Small", parent=_BODY, fontSize=8.5, textColor=colors.HexColor("#555555"))
_RIGHT = ParagraphStyle("Right", parent=_BODY, alignment=TA_RIGHT)
_TITLE = ParagraphStyle("Title", parent=_STYLES["Title"], alignment=TA_RIGHT, fontSize=22)
_HEADING = ParagraphStyle(
    "Heading", parent=_BODY, fontName="Helvetica-Bold", textColor=colors.HexColor("#555555")
)


def safe_text(value: str | None) -> str:
    """Escape user text for a Paragraph and keep line breaks."""
    return escape(value or "").replace("\n", "<br/>")


def format_money(amount: Decimal, currency: str) -> str:
    """Format e.g. Decimal("1234.5") -> "USD 1,234.50" without converting to float."""
    return f"{currency} {amount.quantize(Decimal('0.01')):,.2f}"


def format_quantity(quantity: Decimal) -> str:
    """Format a quantity without trailing zeros, e.g. 2.500 -> "2.5", 3.000 -> "3"."""
    text = f"{quantity.quantize(Decimal('0.001')):f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def pdf_filename(invoice_number: str) -> str:
    """Safe download filename such as INV-0001.pdf."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", invoice_number) + ".pdf"


def _status_label(invoice: Invoice, is_overdue: bool) -> str:
    return "OVERDUE" if is_overdue else invoice.status.upper()


def render_invoice_pdf(invoice: Invoice, seller: User, *, is_overdue: bool = False) -> bytes:
    """
    Render an invoice as a PDF document.

    Args:
        invoice: Invoice with items and client loaded.
        seller: The invoice owner (business details).
        is_overdue: Whether to label the invoice as overdue.

    Returns:
        PDF file content.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice.invoice_number}",
        author=seller.business_name or seller.full_name or "",
    )
    width = doc.width
    currency = invoice.currency
    client = invoice.client

    seller_lines = [f"<b>{safe_text(seller.business_name or seller.full_name)}</b>"]
    if seller.business_address:
        seller_lines.append(safe_text(seller.business_address))
    seller_lines.append(safe_text(seller.email))

    meta_rows = [
        ["Invoice number", invoice.invoice_number],
        ["Status", _status_label(invoice, is_overdue)],
        ["Issue date", invoice.issue_date.isoformat()],
        ["Due date", invoice.due_date.isoformat()],
    ]
    meta = Table(
        [
            [Paragraph(label, _SMALL), Paragraph(safe_text(value), _RIGHT)]
            for label, value in meta_rows
        ],
        colWidths=[30 * mm, 45 * mm],
        hAlign="RIGHT",
    )
    meta.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))

    header = Table(
        [
            [Paragraph("<br/>".join(seller_lines), _BODY), Paragraph("INVOICE", _TITLE)],
            ["", meta],
        ],
        colWidths=[width * 0.5, width * 0.5],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    bill_to = [f"<b>{safe_text(client.name)}</b>"]
    if client.company:
        bill_to.append(safe_text(client.company))
    if client.address:
        bill_to.append(safe_text(client.address))
    bill_to.append(safe_text(client.email))

    item_rows: list[list[Paragraph]] = [
        [
            Paragraph("<b>Description</b>", _BODY),
            Paragraph("<b>Qty</b>", _RIGHT),
            Paragraph("<b>Unit price</b>", _RIGHT),
            Paragraph("<b>Amount</b>", _RIGHT),
        ]
    ]
    for item in invoice.items:
        item_rows.append(
            [
                Paragraph(safe_text(item.description), _BODY),
                Paragraph(format_quantity(item.quantity), _RIGHT),
                Paragraph(format_money(item.unit_price, currency), _RIGHT),
                Paragraph(format_money(item.amount, currency), _RIGHT),
            ]
        )
    items_table = Table(
        item_rows,
        colWidths=[width * 0.46, width * 0.12, width * 0.21, width * 0.21],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    tax_label = f"Tax ({invoice.tax_rate.normalize():f}%)"
    total_rows = [
        ["Subtotal", format_money(invoice.subtotal, currency)],
        [tax_label, format_money(invoice.tax_amount, currency)],
        ["<b>Total</b>", f"<b>{format_money(invoice.total, currency)}</b>"],
    ]
    if invoice.amount_paid > 0:
        total_rows.append(["Amount paid", format_money(invoice.amount_paid, currency)])
        total_rows.append(
            [
                "<b>Balance due</b>",
                f"<b>{format_money(invoice.total - invoice.amount_paid, currency)}</b>",
            ]
        )
    totals_table = Table(
        [[Paragraph(label, _RIGHT), Paragraph(value, _RIGHT)] for label, value in total_rows],
        colWidths=[40 * mm, 45 * mm],
        hAlign="RIGHT",
    )
    totals_table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story = [
        header,
        Spacer(1, 10 * mm),
        Paragraph("BILL TO", _HEADING),
        Spacer(1, 1.5 * mm),
        Paragraph("<br/>".join(bill_to), _BODY),
        Spacer(1, 8 * mm),
        items_table,
        Spacer(1, 4 * mm),
        totals_table,
    ]
    if invoice.notes:
        story += [
            Spacer(1, 8 * mm),
            Paragraph("NOTES", _HEADING),
            Spacer(1, 1.5 * mm),
            Paragraph(safe_text(invoice.notes), _BODY),
        ]

    doc.build(story)
    return buffer.getvalue()
