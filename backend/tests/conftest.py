"""
Test harness.

- Uses TEST_DATABASE_URL (never the development database).
- Migrates the test database once per session with Alembic (downgrade to base, then upgrade to
  head) so migrations are exercised in both directions.
- Each test runs inside a transaction that is rolled back, so tests never see each other's data.
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _test_database_url() -> str:
    url = get_settings().TEST_DATABASE_URL
    if not url:
        pytest.exit("TEST_DATABASE_URL is not set (see .env.example).", returncode=2)
    if url == get_settings().DATABASE_URL:
        pytest.exit("TEST_DATABASE_URL must differ from DATABASE_URL.", returncode=2)
    return url


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Session-wide engine for the migrated test database."""
    url = _test_database_url()
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    test_engine = create_engine(url, pool_pre_ping=True)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """A session whose work (including commits) is rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """HTTP client for the app, wired to the per-test database session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
