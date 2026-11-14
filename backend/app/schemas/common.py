"""Shared schema building blocks: camelCase models, decimal string types, pagination, errors."""

from decimal import Decimal, InvalidOperation
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer, WithJsonSchema
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base for API schemas: camelCase JSON, snake_case Python, readable from ORM objects."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class RequestModel(CamelModel):
    """Base for request bodies: unknown fields are rejected (e.g. client-sent totals)."""

    model_config = ConfigDict(extra="forbid")


def _decimal_from_string(max_places: int) -> BeforeValidator:
    """Build a validator that accepts decimal strings only (JSON numbers are rejected)."""

    def parse(value: object) -> Decimal:
        if isinstance(value, Decimal):
            parsed = value
        elif isinstance(value, str):
            text = value.strip()
            if text != value or not text:
                raise ValueError("must be a decimal string without surrounding spaces")
            try:
                parsed = Decimal(text)
            except InvalidOperation as exc:
                raise ValueError('must be a decimal string, e.g. "10.50"') from exc
        else:
            raise ValueError('must be a decimal string, e.g. "10.50", not a JSON number')
        if not parsed.is_finite():
            raise ValueError("must be a finite number")
        exponent = parsed.as_tuple().exponent
        if isinstance(exponent, int) and -exponent > max_places:
            raise ValueError(f"must have at most {max_places} decimal places")
        return parsed

    return BeforeValidator(parse)


def _decimal_to_string(places: int) -> PlainSerializer:
    """Build a serializer that renders a Decimal as a fixed-places string in JSON."""
    quantum = Decimal(1).scaleb(-places)

    def render(value: Decimal) -> str:
        return str(value.quantize(quantum))

    return PlainSerializer(render, return_type=str, when_used="json")


def _decimal_schema(places: int, example: str) -> WithJsonSchema:
    pattern = rf"^-?\d+(\.\d{{1,{places}}})?$"
    return WithJsonSchema({"type": "string", "pattern": pattern, "examples": [example]})


Money = Annotated[
    Decimal, _decimal_from_string(2), _decimal_to_string(2), _decimal_schema(2, "1250.00")
]
"""Money amount: JSON decimal string with at most 2 places; always serialized with 2 places."""

Quantity = Annotated[
    Decimal, _decimal_from_string(3), _decimal_to_string(3), _decimal_schema(3, "1.500")
]
"""Line-item quantity: JSON decimal string with at most 3 places."""

Rate = Annotated[
    Decimal, _decimal_from_string(2), _decimal_to_string(2), _decimal_schema(2, "8.25")
]
"""Percentage rate such as a tax rate: JSON decimal string with at most 2 places."""


class Page(CamelModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorField(BaseModel):
    """A single field-level validation problem."""

    field: str
    message: str


class ErrorBody(BaseModel):
    """Machine-readable error code plus a human-readable message."""

    code: str
    message: str
    fields: list[ErrorField] = []


class ErrorResponse(BaseModel):
    """Envelope used by every error response."""

    error: ErrorBody
