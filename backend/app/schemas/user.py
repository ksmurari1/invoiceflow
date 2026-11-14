"""User schemas."""

from app.schemas.common import CamelModel, Rate


class UserOut(CamelModel):
    """The current user's profile and invoice defaults."""

    id: int
    email: str
    full_name: str | None
    business_name: str | None
    business_address: str | None
    default_currency: str
    default_tax_rate: Rate
