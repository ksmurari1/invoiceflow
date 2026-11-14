import { Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";

import { ErrorAlert } from "@/components/common/Feedback";
import { FormField } from "@/components/common/FormField";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { CURRENCIES } from "@/lib/constants";
import { fieldErrors } from "@/lib/errors";
import { fieldA11y, optionalText } from "@/lib/forms";
import { calculateTotals } from "@/lib/invoiceTotals";
import { formatMoney } from "@/lib/money";
import type { Client, InvoiceInput } from "@/types/api";

import { type InvoiceFormValues, validateInvoice } from "./invoiceFormModel";

interface InvoiceFormProps {
  clients: Client[];
  initialValues: InvoiceFormValues;
  submitLabel: string;
  submitting: boolean;
  serverError: unknown;
  onSubmit: (input: InvoiceInput) => void;
  onCancel: () => void;
}

const MAX_ITEMS = 100;

export function InvoiceForm({
  clients,
  initialValues,
  submitLabel,
  submitting,
  serverError,
  onSubmit,
  onCancel,
}: InvoiceFormProps) {
  const [values, setValues] = useState<InvoiceFormValues>(initialValues);
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({});
  const nextKey = useRef(Math.max(0, ...initialValues.items.map((i) => i.key)) + 1);

  const serverFieldErrors = fieldErrors(serverError);
  const errors = { ...serverFieldErrors, ...clientErrors };
  const totals = useMemo(
    () => calculateTotals(values.items, values.taxRate),
    [values.items, values.taxRate],
  );

  const set = <K extends keyof InvoiceFormValues>(field: K, value: InvoiceFormValues[K]) =>
    setValues((current) => ({ ...current, [field]: value }));

  const updateItem = (key: number, field: "description" | "quantity" | "unitPrice", value: string) =>
    setValues((current) => ({
      ...current,
      items: current.items.map((item) => (item.key === key ? { ...item, [field]: value } : item)),
    }));

  const addItem = () => {
    const key = nextKey.current++;
    setValues((current) => ({
      ...current,
      items: [...current.items, { key, description: "", quantity: "1", unitPrice: "" }],
    }));
  };

  const removeItem = (key: number) =>
    setValues((current) => ({ ...current, items: current.items.filter((i) => i.key !== key) }));

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const found = validateInvoice(values);
    setClientErrors(found);
    if (Object.keys(found).length > 0) return;
    onSubmit({
      clientId: Number(values.clientId),
      issueDate: values.issueDate,
      dueDate: values.dueDate,
      currency: values.currency,
      taxRate: values.taxRate.trim(),
      notes: optionalText(values.notes),
      items: values.items.map((item) => ({
        description: item.description.trim(),
        quantity: item.quantity.trim(),
        unitPrice: item.unitPrice.trim(),
      })),
    });
  };

  const generalError =
    serverError && Object.keys(serverFieldErrors).length === 0 ? serverError : null;

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      {generalError ? <ErrorAlert error={generalError} title="Could not save invoice" /> : null}
      {Object.keys(clientErrors).length > 0 ? (
        <p role="alert" className="text-sm text-destructive">
          Please fix the highlighted fields.
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <FormField
            id="invoice-client"
            label="Client"
            required
            error={errors.clientId}
            className="sm:col-span-2 lg:col-span-3"
          >
            <NativeSelect
              {...fieldA11y("invoice-client", errors.clientId)}
              value={values.clientId}
              onChange={(e) => set("clientId", e.target.value)}
            >
              <option value="">Select a client…</option>
              {clients.map((client) => (
                <option key={client.id} value={String(client.id)}>
                  {client.company ? `${client.name} (${client.company})` : client.name}
                </option>
              ))}
            </NativeSelect>
          </FormField>
          <FormField id="invoice-issue-date" label="Issue date" required error={errors.issueDate}>
            <Input
              {...fieldA11y("invoice-issue-date", errors.issueDate)}
              type="date"
              value={values.issueDate}
              onChange={(e) => set("issueDate", e.target.value)}
            />
          </FormField>
          <FormField id="invoice-due-date" label="Due date" required error={errors.dueDate}>
            <Input
              {...fieldA11y("invoice-due-date", errors.dueDate)}
              type="date"
              value={values.dueDate}
              min={values.issueDate || undefined}
              onChange={(e) => set("dueDate", e.target.value)}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField id="invoice-currency" label="Currency" error={errors.currency}>
              <NativeSelect
                {...fieldA11y("invoice-currency", errors.currency)}
                value={values.currency}
                onChange={(e) => {
                  const currency = CURRENCIES.find((c) => c === e.target.value);
                  if (currency) set("currency", currency);
                }}
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </NativeSelect>
            </FormField>
            <FormField id="invoice-tax-rate" label="Tax %" error={errors.taxRate}>
              <Input
                {...fieldA11y("invoice-tax-rate", errors.taxRate)}
                inputMode="decimal"
                value={values.taxRate}
                onChange={(e) => set("taxRate", e.target.value)}
              />
            </FormField>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Line items</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {errors.items ? <p className="text-sm text-destructive">{errors.items}</p> : null}
          <div className="hidden gap-3 text-sm font-medium text-muted-foreground md:grid md:grid-cols-[1fr_7rem_9rem_8rem_2.25rem]">
            <span>Description</span>
            <span>Quantity</span>
            <span>Unit price</span>
            <span className="text-right">Amount</span>
            <span />
          </div>
          <ul className="space-y-3">
            {values.items.map((item, index) => {
              const prefix = `items[${index}]`;
              const amount = totals.lineAmounts[index];
              return (
                <li
                  key={item.key}
                  className="grid gap-3 rounded-md border p-3 md:grid-cols-[1fr_7rem_9rem_8rem_2.25rem] md:items-start md:border-0 md:p-0"
                >
                  <FormField
                    id={`item-${item.key}-description`}
                    label={`Line ${index + 1} description`}
                    error={errors[`${prefix}.description`]}
                    className="[&>label]:sr-only"
                  >
                    <Input
                      {...fieldA11y(`item-${item.key}-description`, errors[`${prefix}.description`])}
                      placeholder="Description"
                      value={item.description}
                      maxLength={500}
                      onChange={(e) => updateItem(item.key, "description", e.target.value)}
                    />
                  </FormField>
                  <FormField
                    id={`item-${item.key}-quantity`}
                    label={`Line ${index + 1} quantity`}
                    error={errors[`${prefix}.quantity`]}
                    className="[&>label]:sr-only"
                  >
                    <Input
                      {...fieldA11y(`item-${item.key}-quantity`, errors[`${prefix}.quantity`])}
                      inputMode="decimal"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) => updateItem(item.key, "quantity", e.target.value)}
                    />
                  </FormField>
                  <FormField
                    id={`item-${item.key}-unit-price`}
                    label={`Line ${index + 1} unit price`}
                    error={errors[`${prefix}.unitPrice`]}
                    className="[&>label]:sr-only"
                  >
                    <Input
                      {...fieldA11y(`item-${item.key}-unit-price`, errors[`${prefix}.unitPrice`])}
                      inputMode="decimal"
                      placeholder="0.00"
                      value={item.unitPrice}
                      onChange={(e) => updateItem(item.key, "unitPrice", e.target.value)}
                    />
                  </FormField>
                  <p
                    className="flex h-9 items-center justify-end text-sm tabular-nums"
                    data-testid={`line-amount-${index}`}
                  >
                    {amount ? formatMoney(amount, values.currency) : "—"}
                  </p>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Remove line ${index + 1}`}
                    disabled={values.items.length === 1}
                    onClick={() => removeItem(item.key)}
                  >
                    <Trash2 />
                  </Button>
                </li>
              );
            })}
          </ul>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addItem}
            disabled={values.items.length >= MAX_ITEMS}
          >
            <Plus /> Add line
          </Button>

          <dl
            className="ml-auto grid max-w-xs grid-cols-2 gap-x-6 gap-y-1 pt-4 text-sm"
            aria-label="Totals preview"
          >
            <dt className="text-muted-foreground">Subtotal</dt>
            <dd className="text-right tabular-nums" data-testid="subtotal">
              {formatMoney(totals.subtotal, values.currency)}
            </dd>
            <dt className="text-muted-foreground">Tax</dt>
            <dd className="text-right tabular-nums" data-testid="tax-amount">
              {formatMoney(totals.taxAmount, values.currency)}
            </dd>
            <dt className="font-semibold">Total</dt>
            <dd className="text-right font-semibold tabular-nums" data-testid="total">
              {formatMoney(totals.total, values.currency)}
            </dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <FormField id="invoice-notes" label="Notes" error={errors.notes}>
            <Textarea
              {...fieldA11y("invoice-notes", errors.notes)}
              placeholder="Payment instructions, thank-you note…"
              value={values.notes}
              rows={3}
              maxLength={5000}
              onChange={(e) => set("notes", e.target.value)}
            />
          </FormField>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
