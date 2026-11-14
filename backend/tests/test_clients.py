"""Clients API."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import make_client

VALID: dict[str, Any] = {
    "name": "Globex",
    "email": "ap@globex.example.com",
    "company": "Globex Corporation",
    "address": "10 Main St\nCapital City",
    "notes": "Net 30",
}


def test_create_and_get_client(client: TestClient) -> None:
    created = client.post("/api/v1/clients", json=VALID)

    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Globex"
    assert body["email"] == "ap@globex.example.com"
    assert body["invoiceCount"] == 0
    assert "createdAt" in body

    fetched = client.get(f"/api/v1/clients/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["address"] == "10 Main St\nCapital City"


def test_optional_fields_blank_become_null_and_text_is_trimmed(client: TestClient) -> None:
    response = client.post(
        "/api/v1/clients",
        json={
            "name": "  Initech ",
            "email": " it@initech.example.com ",
            "company": "  ",
            "notes": "",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Initech"
    assert body["email"] == "it@initech.example.com"
    assert body["company"] is None
    assert body["notes"] is None


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({**VALID, "email": "not-an-email"}, "email"),
        ({**VALID, "name": ""}, "name"),
        ({**VALID, "name": "   "}, "name"),
        ({**VALID, "name": "x" * 201}, "name"),
        ({k: v for k, v in VALID.items() if k != "email"}, "email"),
        ({**VALID, "userId": 2}, "userId"),
    ],
)
def test_create_validation(client: TestClient, payload: dict[str, Any], field: str) -> None:
    response = client.post("/api/v1/clients", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert field in [f["field"] for f in error["fields"]]


def test_update_client(client: TestClient) -> None:
    client_id = client.post("/api/v1/clients", json=VALID).json()["id"]

    response = client.put(
        f"/api/v1/clients/{client_id}",
        json={**VALID, "name": "Globex Intl", "company": None},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Globex Intl"
    assert response.json()["company"] is None


def test_delete_client(client: TestClient) -> None:
    client_id = client.post("/api/v1/clients", json=VALID).json()["id"]

    assert client.delete(f"/api/v1/clients/{client_id}").status_code == 204
    assert client.get(f"/api/v1/clients/{client_id}").status_code == 404


def test_missing_client_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/clients/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_list_search_and_pagination(
    client: TestClient, demo_user: User, db_session: Session
) -> None:
    make_client(db_session, demo_user.id, name="beta llc", email="b@x.example.com", company=None)
    make_client(
        db_session, demo_user.id, name="Alpha Inc", email="a@x.example.com", company="100% Co"
    )
    make_client(
        db_session, demo_user.id, name="Gamma", email="g@x.example.com", company="Under_Score"
    )

    everything = client.get("/api/v1/clients").json()
    assert everything["total"] == 3
    assert [c["name"] for c in everything["items"]] == ["Alpha Inc", "beta llc", "Gamma"]

    assert [c["name"] for c in client.get("/api/v1/clients?q=BETA").json()["items"]] == ["beta llc"]
    assert client.get("/api/v1/clients?q=g@x").json()["total"] == 1
    # Wildcards in the search term are matched literally.
    assert [c["name"] for c in client.get("/api/v1/clients?q=%25").json()["items"]] == ["Alpha Inc"]
    assert [c["name"] for c in client.get("/api/v1/clients?q=_").json()["items"]] == ["Gamma"]

    page2 = client.get("/api/v1/clients?page=2&pageSize=2").json()
    assert page2["total"] == 3
    assert page2["page"] == 2
    assert page2["pageSize"] == 2
    assert [c["name"] for c in page2["items"]] == ["Gamma"]


def test_list_rejects_bad_pagination(client: TestClient) -> None:
    assert client.get("/api/v1/clients?pageSize=101").status_code == 422
    assert client.get("/api/v1/clients?page=0").status_code == 422
