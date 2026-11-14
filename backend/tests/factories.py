"""Test data helpers."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.user import User


def make_user(db: Session, **overrides: Any) -> User:
    """Insert a user (flushed, rolled back with the test)."""
    values: dict[str, Any] = {
        "email": f"user-{uuid.uuid4().hex[:10]}@example.com",
        "full_name": "Other User",
        "business_name": "Other Biz",
    }
    values.update(overrides)
    user = User(**values)
    db.add(user)
    db.flush()
    return user


def make_client(db: Session, user_id: int, **overrides: Any) -> Client:
    """Insert a client for the given user."""
    values: dict[str, Any] = {
        "name": "Acme Corp",
        "email": "billing@acme.example.com",
        "company": "Acme",
    }
    values.update(overrides)
    client = Client(user_id=user_id, **values)
    db.add(client)
    db.flush()
    return client


def invoice_payload(
    client_id: int,
    items: Sequence[tuple[str, str]] = (("1", "100.00"),),
    **overrides: Any,
) -> dict[str, Any]:
    """Build a JSON body for POST/PUT /invoices. `items` are (quantity, unitPrice) pairs."""
    payload: dict[str, Any] = {
        "clientId": client_id,
        "issueDate": "2026-03-01",
        "dueDate": "2026-03-31",
        "currency": "USD",
        "taxRate": "0",
        "items": [
            {"description": f"Item {i + 1}", "quantity": qty, "unitPrice": price}
            for i, (qty, price) in enumerate(items)
        ],
    }
    payload.update(overrides)
    return payload
