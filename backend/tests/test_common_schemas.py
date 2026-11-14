"""Decimal string types, camelCase models and the validation error envelope."""

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import Field, ValidationError

from app.errors import AppError, format_location, register_error_handlers
from app.schemas.common import CamelModel, Money, Page, Quantity, Rate, RequestModel


class LineIn(RequestModel):
    unit_price: Money = Field(ge=0)
    quantity: Quantity = Field(gt=0)


class OrderIn(RequestModel):
    tax_rate: Rate = Field(ge=0, le=100)
    items: list[LineIn]


class AmountOut(CamelModel):
    total_amount: Money


# --- Money / Quantity / Rate parsing ---------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0", Decimal("0")),
        ("10", Decimal("10")),
        ("10.5", Decimal("10.5")),
        ("10.50", Decimal("10.50")),
    ],
)
def test_money_accepts_decimal_strings(raw: str, expected: Decimal) -> None:
    line = LineIn.model_validate({"unitPrice": raw, "quantity": "1"})
    assert line.unit_price == expected


@pytest.mark.parametrize(
    "raw",
    [10.5, 10, True, None, "", " 1.00", "abc", "1.001", "NaN", "Infinity", "1e3x"],
)
def test_money_rejects_numbers_and_bad_strings(raw: object) -> None:
    with pytest.raises(ValidationError):
        LineIn.model_validate({"unitPrice": raw, "quantity": "1"})


def test_money_bounds_apply() -> None:
    with pytest.raises(ValidationError):
        LineIn.model_validate({"unitPrice": "-0.01", "quantity": "1"})


def test_quantity_allows_three_places_only() -> None:
    assert LineIn.model_validate({"unitPrice": "1", "quantity": "0.333"}).quantity == Decimal(
        "0.333"
    )
    with pytest.raises(ValidationError):
        LineIn.model_validate({"unitPrice": "1", "quantity": "0.3333"})
    with pytest.raises(ValidationError):
        LineIn.model_validate({"unitPrice": "1", "quantity": "0"})


def test_rate_bounds() -> None:
    assert OrderIn.model_validate({"taxRate": "8.25", "items": []}).tax_rate == Decimal("8.25")
    with pytest.raises(ValidationError):
        OrderIn.model_validate({"taxRate": "100.01", "items": []})


def test_request_model_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        LineIn.model_validate({"unitPrice": "1", "quantity": "1", "amount": "1.00"})


# --- Serialization ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [(Decimal("1250"), "1250.00"), (Decimal("0.5"), "0.50"), (Decimal("10.00"), "10.00")],
)
def test_money_serializes_as_fixed_two_place_string(value: Decimal, expected: str) -> None:
    assert AmountOut(total_amount=value).model_dump(mode="json", by_alias=True) == {
        "totalAmount": expected
    }


def test_quantity_serializes_with_three_places() -> None:
    line = LineIn(unit_price=Decimal("1"), quantity=Decimal("2"))
    assert line.model_dump(mode="json", by_alias=True) == {"unitPrice": "1.00", "quantity": "2.000"}


def test_page_uses_camel_case() -> None:
    page = Page[AmountOut](
        items=[AmountOut(total_amount=Decimal("1"))], total=1, page=1, page_size=20
    )
    assert page.model_dump(mode="json", by_alias=True) == {
        "items": [{"totalAmount": "1.00"}],
        "total": 1,
        "page": 1,
        "pageSize": 20,
    }


def test_money_openapi_schema_is_string() -> None:
    schema = AmountOut.model_json_schema(by_alias=True)
    assert schema["properties"]["totalAmount"]["type"] == "string"


# --- Error envelope --------------------------------------------------------------------------


def _error_app() -> FastAPI:
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.post("/orders")
    async def create_order(order: OrderIn) -> dict[str, str]:
        return {"taxRate": str(order.tax_rate)}

    @test_app.get("/conflict")
    async def conflict() -> None:
        raise AppError(409, "invoice_not_editable", "Only draft invoices can be edited.")

    @test_app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    return test_app


def test_validation_errors_use_envelope_with_field_paths() -> None:
    with TestClient(_error_app()) as test_client:
        response = test_client.post(
            "/orders", json={"taxRate": "5", "items": [{"unitPrice": 10.5, "quantity": "1"}]}
        )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert [f["field"] for f in error["fields"]] == ["items[0].unitPrice"]


def test_app_error_uses_envelope() -> None:
    with TestClient(_error_app()) as test_client:
        response = test_client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "invoice_not_editable",
            "message": "Only draft invoices can be edited.",
            "fields": [],
        }
    }


def test_unhandled_error_hides_details() -> None:
    with TestClient(_error_app(), raise_server_exceptions=False) as test_client:
        response = test_client.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret" not in response.text


@pytest.mark.parametrize(
    ("loc", "expected"),
    [
        (("body", "items", 0, "quantity"), "items[0].quantity"),
        (("query", "page"), "page"),
        (("body",), ""),
        (("email",), "email"),
    ],
)
def test_format_location(loc: tuple[str | int, ...], expected: str) -> None:
    assert format_location(loc) == expected
