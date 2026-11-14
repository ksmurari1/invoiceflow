"""
Current-user dependency — the single authentication seam.

Local MVP: there is no login. Every request acts as the seeded demo user
(settings.DEMO_USER_ID). Real authentication later replaces only this module;
routers and services already receive a `User` and scope every query by `user.id`.
"""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.errors import AppError
from app.models.user import User


async def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Return the user the current request acts as.

    Args:
        db: Database session.

    Returns:
        The active demo user.

    Raises:
        AppError: 401 if the demo user is missing or inactive (database not migrated/seeded).
    """
    user_id = get_settings().DEMO_USER_ID
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise AppError(
            401,
            "not_authenticated",
            "Demo user not found. Run `alembic upgrade head` to create it.",
        )
    return user
