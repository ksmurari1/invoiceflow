import { describe, expect, it } from "vitest";

import { calculateTotals } from "./invoiceTotals";

// Same vectors as backend tests/test_invoice_calc.py
const VECTORS: [string[][], string, string, string, string][] = [
  [[["1", "100.00"]], "0", "100.00", "0.00", "100.00"],
  [[["1.5", "0.33"]], "0", "0.50", "0.00", "0.50"],
  [[["2.5", "19.99"]], "0", "49.98", "0.00", "49.98"],
  [
    [
      ["1", "10.00"],
      ["0.333", "3.00"],
    ],
    "8.25",
    "11.00",
    "0.91",
    "11.91",
  ],
  [[["1", "0.10"]], "5", "0.10", "0.01", "0.11"],
];

describe("calculateTotals", () => {
  it.each(VECTORS)("matches backend vector %#", (items, tax, subtotal, taxAmount, total) => {
    const result = calculateTotals(
      items.map(([quantity = "", unitPrice = ""]) => ({ quantity, unitPrice })),
      tax,
    );
    expect(result).toMatchObject({ subtotal, taxAmount, total, complete: true });
  });

  it("rounds each line half up", () => {
    const result = calculateTotals(
      [
        { quantity: "1.5", unitPrice: "0.33" },
        { quantity: "3", unitPrice: "0.335" },
      ],
      "0",
    );
    expect(result.lineAmounts).toEqual(["0.50", "1.01"]);
  });

  it("treats incomplete lines as zero and reports them", () => {
    const result = calculateTotals(
      [
        { quantity: "2", unitPrice: "10" },
        { quantity: "", unitPrice: "5" },
        { quantity: "1", unitPrice: "abc" },
      ],
      "10",
    );
    expect(result.lineAmounts).toEqual(["20.00", null, null]);
    expect(result.subtotal).toBe("20.00");
    expect(result.taxAmount).toBe("2.00");
    expect(result.total).toBe("22.00");
    expect(result.complete).toBe(false);
  });

  it("handles an empty tax rate", () => {
    const result = calculateTotals([{ quantity: "1", unitPrice: "9.99" }], "");
    expect(result.total).toBe("9.99");
    expect(result.complete).toBe(false);
  });
});
