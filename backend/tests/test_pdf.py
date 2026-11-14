"""Invoice PDF download."""

import io
from decimal import Decimal

from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.pdf import format_money, format_quantity, pdf_filename
from tests.factories import invoice_payload, make_client


def pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_pdf_download_contains_invoice_data(
    client: TestClient, db_session: Session, demo_user: User
) -> None:
    acme = make_client(
        db_session, demo_user.id, name="Acme Corp", address="5 Road\nTown", company="Acme Ltd"
    )
    payload = invoice_payload(
        acme.id,
        items=[("2.5", "19.99"), ("1", "1234.50")],
        taxRate="8.25",
        notes="Thank you for your business.",
    )
    payload["items"][0]["description"] = "Design work"
    payload["items"][1]["description"] = "Hosting"
    invoice = client.post("/api/v1/invoices", json=payload).json()

    response = client.get(f"/api/v1/invoices/{invoice['id']}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="INV-0001.pdf"'
    assert response.content.startswith(b"%PDF-")

    text = pdf_text(response.content)
    for expected in [
        "INVOICE",
        "INV-0001",
        "DRAFT",
        "Demo Studio",
        "1 Example Street",
        "Acme Corp",
        "Acme Ltd",
        "5 Road",
        "2026-03-01",
        "2026-03-31",
        "Design work",
        "Hosting",
        "2.5",
        "USD 19.99",
        "USD 49.98",
        "USD 1,234.50",
        "Subtotal",
        "USD 1,284.48",
        "Tax (8.25%)",
        "USD 105.97",
        "USD 1,390.45",
        "Thank you for your business.",
    ]:
        assert expected in text, f"{expected!r} missing from PDF text"


def test_user_markup_is_printed_literally(
    client: TestClient, db_session: Session, demo_user: User
) -> None:
    nasty = '<b>Bold</b> & <font color="red">x</font> <script>alert(1)</script>'
    acme = make_client(db_session, demo_user.id, name=nasty, company="<i>Co</i>")
    payload = invoice_payload(acme.id, notes="<para>not markup</para>")
    payload["items"][0]["description"] = "Line <br/> one & two"
    invoice = client.post("/api/v1/invoices", json=payload).json()

    response = client.get(f"/api/v1/invoices/{invoice['id']}/pdf")

    assert response.status_code == 200
    text = pdf_text(response.content)
    assert "<b>Bold</b> &" in text
    assert "<script>alert(1)</script>" in text
    assert "<i>Co</i>" in text
    assert "Line <br/> one & two" in text
    assert "<para>not markup</para>" in text


def test_paid_invoice_shows_balance(
    client: TestClient, db_session: Session, demo_user: User
) -> None:
    acme = make_client(db_session, demo_user.id)
    invoice = client.post("/api/v1/invoices", json=invoice_payload(acme.id)).json()
    client.post(f"/api/v1/invoices/{invoice['id']}/send")
    client.post(f"/api/v1/invoices/{invoice['id']}/mark-paid")

    text = pdf_text(client.get(f"/api/v1/invoices/{invoice['id']}/pdf").content)

    assert "PAID" in text
    assert "Amount paid" in text
    assert "Balance due" in text
    assert "USD 0.00" in text


def test_missing_invoice_pdf_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/invoices/999999/pdf").status_code == 404


def test_formatting_helpers() -> None:
    assert format_money(Decimal("1234.5"), "USD") == "USD 1,234.50"
    assert format_money(Decimal("0"), "EUR") == "EUR 0.00"
    assert format_quantity(Decimal("2.500")) == "2.5"
    assert format_quantity(Decimal("3.000")) == "3"
    assert format_quantity(Decimal("10")) == "10"
    assert format_quantity(Decimal("0.333")) == "0.333"
    assert pdf_filename("INV-0001") == "INV-0001.pdf"
    assert pdf_filename('A/B"C') == "A_B_C.pdf"
