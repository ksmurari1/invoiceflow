"""User (account owner). In the local MVP a single seeded demo user owns all data."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    """An account that owns clients and invoices. Business details appear on invoices."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "default_tax_rate >= 0 AND default_tax_rate <= 100", name="default_tax_rate_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    business_name: Mapped[str | None] = mapped_column(String(200))
    business_address: Mapped[str | None] = mapped_column(Text)
    default_currency: Mapped[str] = mapped_column(String(3), server_default="USD")
    default_tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="0")
    is_active: Mapped[bool] = mapped_column(server_default=true())
