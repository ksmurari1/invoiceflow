"""Decimal invoice math (shared vectors with the frontend preview)."""

from decimal import Decimal

import pytest

from app.services.invoice_calc import (
    AmountOutOfRangeError,
    LineInput,
    calculate_totals,
    round_money,
)

D = Decimal

# (items as (qty, unit_price), tax_rate, subtotal, tax, total) — see PRPs/invoiceflow-mvp-plan.md
VECTORS = [
    ([("1", "100.00")], "0", "100.00", "0.00", "100.00"),
    ([("1.5", "0.33")], "0", "0.50", "0.00", "0.50"),
    ([("2.5", "19.99")], "0", "49.98", "0.00", "49.98"),
    ([("1", "10.00"), ("0.333", "3.00")], "8.25", "11.00", "0.91", "11.91"),
    ([("1", "0.10")], "5", "0.10", "0.01", "0.11"),
]


@pytest.mark.parametrize(("items", "tax", "subtotal", "tax_amount", "total"), VECTORS)
def test_shared_vectors(
    items: list[tuple[str, str]], tax: str, subtotal: str, tax_amount: str, total: str
) -> None:
    result = calculate_totals([LineInput(D(q), D(p)) for q, p in items], D(tax))

    assert result.subtotal == D(subtotal)
    assert result.tax_amount == D(tax_amount)
    assert result.total == D(total)
    assert str(result.total) == total  # always exactly 2 places


def test_line_amounts_are_rounded_half_up() -> None:
    result = calculate_totals([LineInput(D("1.5"), D("0.33")), LineInput(D("3"), D("0.335"))], D(0))
    assert result.line_amounts == (D("0.50"), D("1.01"))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0.005", "0.01"),
        ("0.004", "0.00"),
        ("1.005", "1.01"),
        ("2.675", "2.68"),
        ("-0.005", "-0.01"),
    ],
)
def test_round_money_half_up(value: str, expected: str) -> None:
    assert round_money(D(value)) == D(expected)


def test_zero_price_lines_allowed() -> None:
    assert calculate_totals([LineInput(D("2"), D("0"))], D("10")).total == D("0.00")


def test_rejects_amounts_beyond_column_range() -> None:
    with pytest.raises(AmountOutOfRangeError):
        calculate_totals([LineInput(D("1000000"), D("9999999.99"))], D(0))
    with pytest.raises(AmountOutOfRangeError):
        # each line fits, but the taxed total does not
        calculate_totals([LineInput(D("100"), D("9999999.99"))], D("100"))
