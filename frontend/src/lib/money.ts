/**
 * Money helpers. Money values travel as decimal strings ("1250.00") and are handled with
 * decimal.js — never JS numbers — so previews match the server's ROUND_HALF_UP results.
 */
import Decimal from "decimal.js";

import type { DecimalString } from "@/types/api";

const MoneyDecimal = Decimal.clone({ precision: 40, rounding: Decimal.ROUND_HALF_UP });

const DECIMAL_PATTERN = /^-?\d+(\.\d+)?$/;

/** True if the value is a plain decimal string such as "12", "12.5" or "-0.25". */
export function isDecimalString(value: string): boolean {
  return DECIMAL_PATTERN.test(value);
}

/** Parse a decimal string. Throws if the value is not a plain decimal string. */
export function toDecimal(value: DecimalString): Decimal {
  if (!isDecimalString(value)) {
    throw new Error(`Invalid decimal string: "${value}"`);
  }
  return new MoneyDecimal(value);
}

/** Round to 2 decimal places using ROUND_HALF_UP (same rule as the backend). */
export function roundMoney(value: Decimal): Decimal {
  return value.toDecimalPlaces(2, Decimal.ROUND_HALF_UP);
}

/** Round and render as a 2-place decimal string, e.g. "1250.00". */
export function toMoneyString(value: Decimal): DecimalString {
  return roundMoney(value).toFixed(2);
}

/** Add decimal strings exactly and return a 2-place money string. */
export function addMoney(...values: DecimalString[]): DecimalString {
  const total = values.reduce((sum, value) => sum.plus(toDecimal(value)), new MoneyDecimal(0));
  return toMoneyString(total);
}

/**
 * Format a money string for display, e.g. formatMoney("1234.5", "USD") -> "$1,234.50".
 * The string is passed to Intl.NumberFormat directly, so no float conversion happens.
 */
export function formatMoney(value: DecimalString, currency: string, locale = "en-US"): string {
  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return formatter.format(toMoneyString(toDecimal(value)) as Intl.StringNumericLiteral);
}
