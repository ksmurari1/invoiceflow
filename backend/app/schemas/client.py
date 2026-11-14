"""Client request/response schemas."""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import CamelModel, RequestModel


class ClientIn(RequestModel):
    """Create or fully replace a client."""

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    company: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name", "email", mode="before")
    @classmethod
    def strip_required(cls, value: object) -> object:
        """Trim surrounding whitespace from required text fields."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("company", "address", "notes", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        """Trim optional text fields and store empty strings as null."""
        if isinstance(value, str):
            return value.strip() or None
        return value


class ClientOut(CamelModel):
    """A client as returned by the API."""

    id: int
    name: str
    email: str
    company: str | None
    address: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ClientDetailOut(ClientOut):
    """A client with a summary of its invoices."""

    invoice_count: int
