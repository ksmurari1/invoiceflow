/**
 * Live totals preview for the invoice form. Mirrors backend app/services/invoice_calc.py:
 *
 *   item.amount = round(quantity * unitPrice)
 *   subtotal    = sum(item.amount)
 *   taxAmount   = round(subtotal * taxRate / 100)
 *   total       = subtotal + taxAmount        (round = 2 places, ROUND_HALF_UP)
 *
 * Preview only — the server recomputes and stores the authoritative totals.
 */
import Decimal from "decimal.js";

import type { DecimalString } from "@/types/api";

import { isDecimalString, roundMoney, toDecimal } from "./money";

export interface LineValues {
  quantity: string;
  unitPrice: string;
}

export interface TotalsPreview {
  /** Rounded amount per line, or null when that line's inputs are not valid numbers yet. */
  lineAmounts: (DecimalString | null)[];
  subtotal: DecimalString;
  taxAmount: DecimalString;
  total: DecimalString;
  /** False if any line or the tax rate could not be parsed (they count as 0 meanwhile). */
  complete: boolean;
}

function parse(value: string): Decimal | null {
  const text = value.trim();
  return isDecimalString(text) ? toDecimal(text) : null;
}

export function calculateTotals(lines: LineValues[], taxRate: string): TotalsPreview {
  let complete = true;
  let subtotal = new Decimal(0);

  const lineAmounts = lines.map((line) => {
    const quantity = parse(line.quantity);
    const unitPrice = parse(line.unitPrice);
    if (!quantity || !unitPrice) {
      complete = false;
      return null;
    }
    const amount = roundMoney(quantity.times(unitPrice));
    subtotal = subtotal.plus(amount);
    return amount.toFixed(2);
  });

  const rate = parse(taxRate);
  if (!rate) {
    complete = false;
  }
  const taxAmount = roundMoney(subtotal.times(rate ?? 0).dividedBy(100));
  const total = subtotal.plus(taxAmount);

  return {
    lineAmounts,
    subtotal: subtotal.toFixed(2),
    taxAmount: taxAmount.toFixed(2),
    total: total.toFixed(2),
    complete,
  };
}
