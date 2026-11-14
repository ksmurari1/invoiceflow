import { DEFAULT_PAYMENT_DAYS } from "@/lib/constants";
import { addDaysIso, formatQuantity, todayIso } from "@/lib/format";
import { isDecimalString, toDecimal } from "@/lib/money";
import type { Currency, Invoice } from "@/types/api";

export interface LineDraft {
  key: number;
  description: string;
  quantity: string;
  unitPrice: string;
}

export interface InvoiceFormValues {
  clientId: string;
  issueDate: string;
  dueDate: string;
  currency: Currency;
  taxRate: string;
  notes: string;
  items: LineDraft[];
}

/** Values for a new invoice, using the user's defaults. */
export function newInvoiceValues(defaults: {
  clientId?: string;
  currency: Currency;
  taxRate: string;
}): InvoiceFormValues {
  const issueDate = todayIso();
  return {
    clientId: defaults.clientId ?? "",
    issueDate,
    dueDate: addDaysIso(issueDate, DEFAULT_PAYMENT_DAYS),
    currency: defaults.currency,
    taxRate: formatQuantity(defaults.taxRate),
    notes: "",
    items: [{ key: 1, description: "", quantity: "1", unitPrice: "" }],
  };
}

/** Values for editing an existing (draft) invoice. */
export function invoiceToValues(invoice: Invoice): InvoiceFormValues {
  return {
    clientId: String(invoice.clientId),
    issueDate: invoice.issueDate,
    dueDate: invoice.dueDate,
    currency: invoice.currency,
    taxRate: formatQuantity(invoice.taxRate),
    notes: invoice.notes ?? "",
    items: invoice.items.map((item, index) => ({
      key: index + 1,
      description: item.description,
      quantity: formatQuantity(item.quantity),
      unitPrice: item.unitPrice,
    })),
  };
}

function decimalPlaces(value: string): number {
  const [, fraction = ""] = value.split(".");
  return fraction.length;
}

/** Client-side checks that mirror the API rules (the server re-validates everything). */
export function validateInvoice(values: InvoiceFormValues): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!values.clientId) errors.clientId = "Choose a client.";
  if (!values.issueDate) errors.issueDate = "Issue date is required.";
  if (!values.dueDate) errors.dueDate = "Due date is required.";
  else if (values.issueDate && values.dueDate < values.issueDate) {
    errors.dueDate = "Due date must be on or after the issue date.";
  }

  const tax = values.taxRate.trim();
  if (!isDecimalString(tax) || decimalPlaces(tax) > 2) {
    errors.taxRate = "Enter a percentage like 8.25.";
  } else if (toDecimal(tax).lessThan(0) || toDecimal(tax).greaterThan(100)) {
    errors.taxRate = "Tax rate must be between 0 and 100.";
  }

  if (values.items.length === 0) errors.items = "Add at least one line item.";
  values.items.forEach((item, index) => {
    const prefix = `items[${index}]`;
    if (!item.description.trim()) errors[`${prefix}.description`] = "Required.";
    const qty = item.quantity.trim();
    if (!isDecimalString(qty) || decimalPlaces(qty) > 3 || !toDecimal(qty).greaterThan(0)) {
      errors[`${prefix}.quantity`] = "Quantity > 0, up to 3 decimals.";
    }
    const price = item.unitPrice.trim();
    if (!isDecimalString(price) || decimalPlaces(price) > 2 || toDecimal(price).lessThan(0)) {
      errors[`${prefix}.unitPrice`] = "Price ≥ 0, up to 2 decimals.";
    }
  });
  return errors;
}
