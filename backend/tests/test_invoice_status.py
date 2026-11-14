"""Status transitions and computed overdue."""

from datetime import UTC, datetime
from typing import Any

import pytest
import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import invoice_payload, make_client

ACTIONS = ("send", "mark-paid", "void")


@pytest.fixture
def new_invoice(client: TestClient, db_session: Session, demo_user: User) -> dict[str, Any]:
    acme = make_client(db_session, demo_user.id)
    response = client.post("/api/v1/invoices", json=invoice_payload(acme.id))
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


def act(client: TestClient, invoice_id: int, action: str) -> Any:
    return client.post(f"/api/v1/invoices/{invoice_id}/{action}")


def test_happy_path_draft_sent_paid(client: TestClient, new_invoice: dict[str, Any]) -> None:
    sent = act(client, new_invoice["id"], "send")
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"
    assert sent.json()["sentAt"] is not None

    paid = act(client, new_invoice["id"], "mark-paid")
    assert paid.status_code == 200
    body = paid.json()
    assert body["status"] == "paid"
    assert body["amountPaid"] == body["total"]
    assert body["balanceDue"] == "0.00"
    assert body["paidAt"] is not None


@pytest.mark.parametrize(
    ("setup", "action", "allowed"),
    [
        ([], "send", True),
        ([], "mark-paid", False),
        ([], "void", True),
        (["send"], "send", False),
        (["send"], "mark-paid", True),
        (["send"], "void", True),
        (["send", "mark-paid"], "send", False),
        (["send", "mark-paid"], "mark-paid", False),
        (["send", "mark-paid"], "void", False),
        (["void"], "send", False),
        (["void"], "mark-paid", False),
        (["void"], "void", False),
    ],
)
def test_transition_matrix(
    client: TestClient,
    new_invoice: dict[str, Any],
    setup: list[str],
    action: str,
    allowed: bool,
) -> None:
    for step in setup:
        assert act(client, new_invoice["id"], step).status_code == 200

    response = act(client, new_invoice["id"], action)

    if allowed:
        assert response.status_code == 200
    else:
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "invalid_status_transition"


@pytest.mark.parametrize("setup", [["send"], ["send", "mark-paid"], ["void"]])
def test_non_draft_cannot_be_edited_or_deleted(
    client: TestClient, new_invoice: dict[str, Any], setup: list[str]
) -> None:
    for step in setup:
        act(client, new_invoice["id"], step)

    put = client.put(
        f"/api/v1/invoices/{new_invoice['id']}", json=invoice_payload(new_invoice["clientId"])
    )
    delete = client.delete(f"/api/v1/invoices/{new_invoice['id']}")

    assert put.status_code == 409
    assert put.json()["error"]["code"] == "invoice_not_editable"
    assert delete.status_code == 409


def test_overdue_is_computed_from_due_date(client: TestClient, new_invoice: dict[str, Any]) -> None:
    # Factory invoice is due 2026-03-31.
    act(client, new_invoice["id"], "send")

    with time_machine.travel(datetime(2026, 3, 31, 23, tzinfo=UTC), tick=False):
        assert client.get(f"/api/v1/invoices/{new_invoice['id']}").json()["isOverdue"] is False
        assert client.get("/api/v1/invoices?status=overdue").json()["total"] == 0

    with time_machine.travel(datetime(2026, 4, 1, 0, 1, tzinfo=UTC), tick=False):
        detail = client.get(f"/api/v1/invoices/{new_invoice['id']}").json()
        assert detail["status"] == "sent"
        assert detail["isOverdue"] is True
        overdue = client.get("/api/v1/invoices?status=overdue").json()
        assert [i["id"] for i in overdue["items"]] == [new_invoice["id"]]
        assert overdue["items"][0]["isOverdue"] is True

        # Overdue invoices can still be paid; paid invoices are never overdue.
        assert act(client, new_invoice["id"], "mark-paid").json()["isOverdue"] is False


def test_drafts_are_never_overdue(client: TestClient, new_invoice: dict[str, Any]) -> None:
    with time_machine.travel(datetime(2027, 1, 1, tzinfo=UTC), tick=False):
        assert client.get(f"/api/v1/invoices/{new_invoice['id']}").json()["isOverdue"] is False
