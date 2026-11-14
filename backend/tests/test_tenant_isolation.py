"""
Multi-tenant isolation: another user can never see or change the demo user's data.

Every /api/v1 route with a path id is discovered from the app, so new routes are covered
automatically.
"""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from tests.factories import invoice_payload, make_client, make_user


def id_routes() -> list[tuple[str, str]]:
    """(METHOD, path) for every /api/v1 operation that takes a path id, from the OpenAPI schema."""
    routes: list[tuple[str, str]] = []
    for path, operations in app.openapi()["paths"].items():
        if path.startswith("/api/v1") and "{" in path:
            routes.extend((method.upper(), path) for method in sorted(operations))
    return routes


def test_discovers_id_routes() -> None:
    routes = set(id_routes())
    assert ("DELETE", "/api/v1/clients/{client_id}") in routes
    assert ("GET", "/api/v1/invoices/{invoice_id}/pdf") in routes
    assert len(routes) == 10


@pytest.mark.parametrize(("method", "path"), id_routes())
def test_other_user_gets_404_on_every_id_route(
    client: TestClient,
    db_session: Session,
    demo_user: User,
    act_as: Callable[[User], None],
    method: str,
    path: str,
) -> None:
    acme = make_client(db_session, demo_user.id)
    invoice = client.post("/api/v1/invoices", json=invoice_payload(acme.id)).json()

    act_as(make_user(db_session))
    url = path.format(client_id=acme.id, invoice_id=invoice["id"])
    body: dict[str, Any] | None = None
    if method == "PUT" and "{client_id}" in path:
        body = {"name": "Hijack", "email": "x@example.com"}
    elif method == "PUT":
        body = invoice_payload(acme.id)

    response = client.request(method, url, json=body)

    assert response.status_code == 404, f"{method} {path} -> {response.status_code}"
    assert response.json()["error"]["code"] == "not_found"


def test_lists_and_dashboard_only_show_own_data(
    client: TestClient, db_session: Session, demo_user: User, act_as: Callable[[User], None]
) -> None:
    acme = make_client(db_session, demo_user.id)
    client.post("/api/v1/invoices", json=invoice_payload(acme.id))

    act_as(make_user(db_session))

    assert client.get("/api/v1/clients").json()["total"] == 0
    assert client.get("/api/v1/invoices").json()["total"] == 0
    assert client.get(f"/api/v1/invoices?clientId={acme.id}").json()["total"] == 0
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["clientCount"] == 0
    assert summary["invoiceCount"] == 0


def test_cannot_invoice_another_users_client(
    client: TestClient, db_session: Session, demo_user: User, act_as: Callable[[User], None]
) -> None:
    acme = make_client(db_session, demo_user.id)
    act_as(make_user(db_session))

    response = client.post("/api/v1/invoices", json=invoice_payload(acme.id))

    assert response.status_code == 404
