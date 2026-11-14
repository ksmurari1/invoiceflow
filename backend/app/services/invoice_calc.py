"""
Invoice money math — the single source of truth for totals.

    round(x)    = x.quantize(0.01, ROUND_HALF_UP)
    item.amount = round(quantity * unit_price)
    subtotal    = sum(item.amount)
    tax_amount  = round(subtotal * tax_rate / 100)
    total       = subtotal + tax_amount

Pure functions on Decimal; no floats anywhere.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
HUNDRED = Decimal(100)
MAX_AMOUNT = Decimal("999999999.99")


class AmountOutOfRangeError(ValueError):
    """A computed amount exceeds what an invoice may hold."""


@dataclass(frozen=True)
class LineInput:
    """Quantity and unit price of one invoice line."""

    quantity: Decimal
    unit_price: Decimal


@dataclass(frozen=True)
class InvoiceTotals:
    """Computed amounts for an invoice."""

    line_amounts: tuple[Decimal, ...]
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal


def round_money(value: Decimal) -> Decimal:
    """
    Round to cents using ROUND_HALF_UP.

    Args:
        value: Any Decimal.

    Returns:
        Value rounded to 2 decimal places (0.005 -> 0.01).
    """
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_totals(lines: Sequence[LineInput], tax_rate: Decimal) -> InvoiceTotals:
    """
    Compute line amounts, subtotal, tax and total for an invoice.

    Args:
        lines: Invoice lines (quantity > 0, unit_price >= 0 — validated by the caller).
        tax_rate: Tax percentage, e.g. Decimal("8.25").

    Returns:
        InvoiceTotals with every amount rounded to cents.

    Raises:
        AmountOutOfRangeError: If a line amount or the total exceeds MAX_AMOUNT.
    """
    line_amounts = tuple(round_money(line.quantity * line.unit_price) for line in lines)
    if any(amount > MAX_AMOUNT for amount in line_amounts):
        raise AmountOutOfRangeError("A line amount exceeds the maximum invoice amount.")
    subtotal = sum(line_amounts, Decimal("0.00"))
    tax_amount = round_money(subtotal * tax_rate / HUNDRED)
    total = subtotal + tax_amount
    if total > MAX_AMOUNT:
        raise AmountOutOfRangeError("The invoice total exceeds the maximum invoice amount.")
    return InvoiceTotals(
        line_amounts=line_amounts, subtotal=subtotal, tax_amount=tax_amount, total=total
    )
