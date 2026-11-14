"""Dashboard summary."""

from datetime import UTC, datetime
from typing import Any

import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import invoice_payload, make_client, make_user


def create(client: TestClient, payload: dict[str, Any]) -> int:
    response = client.post("/api/v1/invoices", json=payload)
    assert response.status_code == 201, response.text
    invoice_id: int = response.json()["id"]
    return invoice_id


def test_empty_dashboard(client: TestClient) -> None:
    body = client.get("/api/v1/dashboard/summary").json()

    assert body == {"clientCount": 0, "invoiceCount": 0, "currencies": [], "recentInvoices": []}


@time_machine.travel(datetime(2026, 4, 15, tzinfo=UTC), tick=False)
def test_summary_matches_invoices(client: TestClient, db_session: Session, demo_user: User) -> None:
    acme = make_client(db_session, demo_user.id)
    make_client(db_session, demo_user.id, name="Unused")

    # USD: draft 100, sent-not-due 200, sent-overdue 50 + 25, paid 300, void 999
    create(client, invoice_payload(acme.id, items=[("1", "100.00")]))
    on_time = create(
        client, invoice_payload(acme.id, items=[("1", "200.00")], dueDate="2026-05-01")
    )
    late1 = create(client, invoice_payload(acme.id, items=[("1", "50.00")], dueDate="2026-04-01"))
    late2 = create(client, invoice_payload(acme.id, items=[("1", "25.00")], dueDate="2026-04-14"))
    paid = create(client, invoice_payload(acme.id, items=[("1", "300.00")]))
    void = create(client, invoice_payload(acme.id, items=[("1", "999.00")]))
    for invoice_id in (on_time, late1, late2, paid):
        client.post(f"/api/v1/invoices/{invoice_id}/send")
    client.post(f"/api/v1/invoices/{paid}/mark-paid")
    client.post(f"/api/v1/invoices/{void}/void")
    # EUR: one draft
    create(client, invoice_payload(acme.id, items=[("2", "10.00")], currency="EUR"))

    # Another user's data must not leak in.
    other = make_user(db_session)
    make_client(db_session, other.id)

    body = client.get("/api/v1/dashboard/summary").json()

    assert body["clientCount"] == 2
    assert body["invoiceCount"] == 7
    assert [c["currency"] for c in body["currencies"]] == ["USD", "EUR"]
    usd = body["currencies"][0]
    assert usd["draft"] == {"count": 1, "amount": "100.00"}
    assert usd["outstanding"] == {"count": 3, "amount": "275.00"}
    assert usd["overdue"] == {"count": 2, "amount": "75.00"}
    assert usd["paid"] == {"count": 1, "amount": "300.00"}
    eur = body["currencies"][1]
    assert eur["draft"] == {"count": 1, "amount": "20.00"}
    assert eur["paid"] == {"count": 0, "amount": "0.00"}

    recent = body["recentInvoices"]
    assert len(recent) == 5
    assert recent[0]["currency"] == "EUR"  # most recently created first
    assert {r["isOverdue"] for r in recent if r["id"] in (late1, late2)} == {True}
