"""Invoice CRUD, validation and server-side totals."""

from datetime import UTC, datetime
from typing import Any

import pytest
import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.user import User
from tests.factories import invoice_payload, make_client


@pytest.fixture
def acme(db_session: Session, demo_user: User) -> Client:
    return make_client(db_session, demo_user.id)


def create(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/v1/invoices", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def test_create_computes_totals_and_numbers(client: TestClient, acme: Client) -> None:
    body = create(
        client,
        invoice_payload(acme.id, items=[("1", "10.00"), ("0.333", "3.00")], taxRate="8.25"),
    )

    assert body["invoiceNumber"] == "INV-0001"
    assert body["status"] == "draft"
    assert body["isOverdue"] is False
    assert body["subtotal"] == "11.00"
    assert body["taxRate"] == "8.25"
    assert body["taxAmount"] == "0.91"
    assert body["total"] == "11.91"
    assert body["amountPaid"] == "0.00"
    assert body["balanceDue"] == "11.91"
    assert [i["amount"] for i in body["items"]] == ["10.00", "1.00"]
    assert [i["quantity"] for i in body["items"]] == ["1.000", "0.333"]
    assert [i["position"] for i in body["items"]] == [0, 1]
    assert body["client"]["name"] == "Acme Corp"

    second = create(client, invoice_payload(acme.id))
    assert second["invoiceNumber"] == "INV-0002"


@time_machine.travel(datetime(2026, 5, 10, 12, tzinfo=UTC), tick=False)
def test_defaults_from_user_and_today(
    client: TestClient, acme: Client, demo_user: User, db_session: Session
) -> None:
    demo_user.default_currency = "EUR"
    demo_user.default_tax_rate = 20  # type: ignore[assignment]
    db_session.flush()
    payload = invoice_payload(acme.id)
    for key in ("issueDate", "dueDate", "currency", "taxRate"):
        payload.pop(key)

    body = create(client, payload)

    assert body["issueDate"] == "2026-05-10"
    assert body["dueDate"] == "2026-06-09"
    assert body["currency"] == "EUR"
    assert body["taxRate"] == "20.00"
    assert body["total"] == "120.00"


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"items": []}, "items"),
        ({"taxRate": "100.01"}, "taxRate"),
        ({"taxRate": 5}, "taxRate"),
        ({"currency": "JPY"}, "currency"),
        ({"total": "1.00"}, "total"),
        ({"items": [{"description": "x", "quantity": "0", "unitPrice": "1"}]}, "items[0].quantity"),
        (
            {"items": [{"description": "x", "quantity": "1", "unitPrice": "-1"}]},
            "items[0].unitPrice",
        ),
        (
            {"items": [{"description": "x", "quantity": "1", "unitPrice": 10.5}]},
            "items[0].unitPrice",
        ),
        (
            {"items": [{"description": "x", "quantity": "1", "unitPrice": "1.001"}]},
            "items[0].unitPrice",
        ),
        (
            {"items": [{"description": " ", "quantity": "1", "unitPrice": "1"}]},
            "items[0].description",
        ),
        (
            {"items": [{"description": "x", "quantity": "1", "unitPrice": "1", "amount": "1"}]},
            "items[0].amount",
        ),
    ],
)
def test_validation_errors(
    client: TestClient, acme: Client, changes: dict[str, Any], field: str
) -> None:
    response = client.post("/api/v1/invoices", json={**invoice_payload(acme.id), **changes})

    assert response.status_code == 422
    assert field in [f["field"] for f in response.json()["error"]["fields"]]


def test_too_many_items(client: TestClient, acme: Client) -> None:
    response = client.post(
        "/api/v1/invoices", json=invoice_payload(acme.id, items=[("1", "1")] * 101)
    )
    assert response.status_code == 422


def test_due_date_before_issue_date(client: TestClient, acme: Client) -> None:
    response = client.post(
        "/api/v1/invoices",
        json=invoice_payload(acme.id, issueDate="2026-03-10", dueDate="2026-03-09"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["fields"] == [
        {"field": "dueDate", "message": "must be on or after the issue date"}
    ]


def test_amount_out_of_range(client: TestClient, acme: Client) -> None:
    response = client.post(
        "/api/v1/invoices", json=invoice_payload(acme.id, items=[("1000000", "9999999.99")])
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "amount_out_of_range"


def test_unknown_client_is_404(client: TestClient) -> None:
    response = client.post("/api/v1/invoices", json=invoice_payload(999999))
    assert response.status_code == 404


def test_update_draft_replaces_items_and_keeps_number(client: TestClient, acme: Client) -> None:
    body = create(client, invoice_payload(acme.id, items=[("1", "5.00"), ("2", "5.00")]))
    other = make_client_via_api(client, "Beta")

    response = client.put(
        f"/api/v1/invoices/{body['id']}",
        json=invoice_payload(other, items=[("3", "2.50")], taxRate="10", notes="Thanks!"),
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["invoiceNumber"] == body["invoiceNumber"]
    assert updated["clientId"] == other
    assert updated["client"]["name"] == "Beta"
    assert len(updated["items"]) == 1
    assert updated["items"][0]["amount"] == "7.50"
    assert updated["total"] == "8.25"
    assert updated["notes"] == "Thanks!"


def test_delete_draft(client: TestClient, acme: Client) -> None:
    body = create(client, invoice_payload(acme.id))

    assert client.delete(f"/api/v1/invoices/{body['id']}").status_code == 204
    assert client.get(f"/api/v1/invoices/{body['id']}").status_code == 404
    # numbers are never reused
    assert create(client, invoice_payload(acme.id))["invoiceNumber"] == "INV-0002"


def test_list_filters_and_pagination(client: TestClient, acme: Client) -> None:
    beta = make_client_via_api(client, "Beta")
    a = create(client, invoice_payload(acme.id, issueDate="2026-01-01", dueDate="2026-01-31"))
    b = create(client, invoice_payload(beta, issueDate="2026-02-01", dueDate="2026-02-28"))
    c = create(client, invoice_payload(acme.id, issueDate="2026-03-01", dueDate="2026-03-31"))
    client.post(f"/api/v1/invoices/{b['id']}/send")

    listing = client.get("/api/v1/invoices").json()
    assert listing["total"] == 3
    assert [i["id"] for i in listing["items"]] == [c["id"], b["id"], a["id"]]
    assert listing["items"][1]["clientName"] == "Beta"

    assert [i["id"] for i in client.get("/api/v1/invoices?status=sent").json()["items"]] == [
        b["id"]
    ]
    by_client = client.get(f"/api/v1/invoices?clientId={acme.id}").json()
    assert {i["id"] for i in by_client["items"]} == {a["id"], c["id"]}

    page = client.get("/api/v1/invoices?page=2&pageSize=2").json()
    assert [i["id"] for i in page["items"]] == [a["id"]]

    assert client.get("/api/v1/invoices?status=bogus").status_code == 422


def test_client_delete_rules(client: TestClient, acme: Client) -> None:
    draft = create(client, invoice_payload(acme.id))
    beta = make_client_via_api(client, "Beta")
    sent = create(client, invoice_payload(beta))
    client.post(f"/api/v1/invoices/{sent['id']}/send")

    detail = client.get(f"/api/v1/clients/{acme.id}").json()
    assert detail["invoiceCount"] == 1

    # Drafts are deleted together with the client.
    assert client.delete(f"/api/v1/clients/{acme.id}").status_code == 204
    assert client.get(f"/api/v1/invoices/{draft['id']}").status_code == 404

    # A client with a non-draft invoice cannot be deleted.
    response = client.delete(f"/api/v1/clients/{beta}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "client_has_invoices"


def make_client_via_api(client: TestClient, name: str) -> int:
    response = client.post(
        "/api/v1/clients", json={"name": name, "email": f"{name.lower()}@example.com"}
    )
    assert response.status_code == 201
    client_id: int = response.json()["id"]
    return client_id
