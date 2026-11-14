import { describe, expect, it } from "vitest";

import { addMoney, formatMoney, isDecimalString, toDecimal, toMoneyString } from "./money";

describe("money helpers", () => {
  it("validates decimal strings", () => {
    expect(isDecimalString("12")).toBe(true);
    expect(isDecimalString("12.50")).toBe(true);
    expect(isDecimalString("-0.25")).toBe(true);
    expect(isDecimalString("1e3")).toBe(false);
    expect(isDecimalString("12.")).toBe(false);
    expect(isDecimalString(" 1")).toBe(false);
    expect(isDecimalString("")).toBe(false);
    expect(() => toDecimal("abc")).toThrow();
  });

  it("rounds half up like the backend", () => {
    // A float would turn 1.005 into 1.00499999...; Decimal keeps it exact.
    expect(toMoneyString(toDecimal("1.005"))).toBe("1.01");
    expect(toMoneyString(toDecimal("0.005"))).toBe("0.01");
    expect(toMoneyString(toDecimal("0.004"))).toBe("0.00");
    expect(toMoneyString(toDecimal("-0.005"))).toBe("-0.01");
    expect(toMoneyString(toDecimal("12"))).toBe("12.00");
  });

  it("adds without floating point error", () => {
    expect(addMoney("0.10", "0.20")).toBe("0.30");
    expect(addMoney("9999999999.99", "0.01")).toBe("10000000000.00");
    expect(addMoney()).toBe("0.00");
  });

  it("formats for display without float conversion", () => {
    expect(formatMoney("1234.5", "USD")).toBe("$1,234.50");
    expect(formatMoney("0", "EUR", "en-US")).toBe("€0.00");
    expect(formatMoney("12345678901234.56", "USD")).toBe("$12,345,678,901,234.56");
  });
});
