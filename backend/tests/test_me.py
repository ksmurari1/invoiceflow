"""Demo-user auth seam and /me."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import create_app
from app.models.user import User


def test_me_returns_demo_user(client: TestClient, demo_user: User) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == demo_user.id
    assert body["businessName"] == "Demo Studio"
    assert body["defaultCurrency"] == "USD"
    assert body["defaultTaxRate"] == "0.00"


def test_inactive_demo_user_is_rejected(
    client: TestClient, demo_user: User, db_session: Session
) -> None:
    demo_user.is_active = False
    db_session.flush()

    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_refuses_to_start_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="local use only"):
            create_app()
    finally:
        get_settings.cache_clear()
