"""users (+ local demo user)

Revision ID: 0001
Revises:
Create Date: 2026-11-14 16:41:33.331284
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEMO_USER_ID = 1


def upgrade() -> None:
    """Create the users table and seed the local demo user (id=1)."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("business_name", sa.String(length=200), nullable=True),
        sa.Column("business_address", sa.Text(), nullable=True),
        sa.Column("default_currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column(
            "default_tax_rate",
            sa.Numeric(precision=5, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "default_tax_rate >= 0 AND default_tax_rate <= 100",
            name=op.f("ck_users_default_tax_rate_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.execute(
        sa.text(
            "INSERT INTO users (id, email, full_name, business_name, business_address) "
            "VALUES (:id, :email, :full_name, :business_name, :business_address)"
        ).bindparams(
            id=DEMO_USER_ID,
            email="demo@invoiceflow.local",
            full_name="Demo User",
            business_name="Demo Studio",
            business_address="1 Example Street\nSpringfield",
        )
    )
    # The row above used an explicit id; move the sequence past it.
    op.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users))")


def downgrade() -> None:
    """Drop the users table (and the demo user)."""
    op.drop_table("users")
