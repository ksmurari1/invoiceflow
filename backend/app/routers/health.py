"""Liveness and database health check (unprefixed: GET /health)."""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import CamelModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(CamelModel):
    """Health check result."""

    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "Database unavailable"}},
)
async def health(response: Response, db: Session = Depends(get_db)) -> HealthResponse:
    """
    Report API liveness and whether the database answers a trivial query.

    Returns:
        200 with `{"status": "ok", "database": "ok"}`, or 503 when the database is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check: database unavailable")
        response.status_code = 503
        return HealthResponse(status="degraded", database="unavailable")
    return HealthResponse(status="ok", database="ok")
