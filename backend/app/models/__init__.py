"""ORM models. Every model module must be imported here so Alembic autogenerate can see it."""

from app.database import Base

__all__ = ["Base"]
