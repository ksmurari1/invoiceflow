"""Client: a person or company the user bills."""

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Client(TimestampMixin, Base):
    """A billable client owned by exactly one user."""

    __tablename__ = "clients"
    __table_args__ = (
        # Target of the composite FK from invoices: an invoice may only reference
        # a client that belongs to the same user.
        UniqueConstraint("id", "user_id"),
        Index("ix_clients_user_id_name", "user_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254))
    company: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
