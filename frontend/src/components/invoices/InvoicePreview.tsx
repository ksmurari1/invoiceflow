import { formatDate, formatQuantity } from "@/lib/format";
import { formatMoney } from "@/lib/money";
import type { Invoice, User } from "@/types/api";

import { StatusBadge } from "./StatusBadge";

interface InvoicePreviewProps {
  invoice: Invoice;
  seller: User | undefined;
}

/** Document-style invoice preview. Shows the same data as the PDF. */
export function InvoicePreview({ invoice, seller }: InvoicePreviewProps) {
  const money = (value: string) => formatMoney(value, invoice.currency);
  const hasPayment = invoice.amountPaid !== "0.00";

  return (
    <article
      aria-label={`Invoice ${invoice.invoiceNumber}`}
      className="rounded-xl border bg-card p-6 text-sm text-card-foreground shadow-sm sm:p-10"
    >
      <header className="flex flex-col gap-6 sm:flex-row sm:justify-between">
        <div className="space-y-1">
          <p className="text-base font-semibold">
            {seller?.businessName ?? seller?.fullName ?? "Your business"}
          </p>
          {seller?.businessAddress ? (
            <p className="whitespace-pre-line text-muted-foreground">{seller.businessAddress}</p>
          ) : null}
          {seller ? <p className="text-muted-foreground">{seller.email}</p> : null}
        </div>
        <div className="space-y-2 sm:text-right">
          <p className="text-3xl font-semibold tracking-tight">INVOICE</p>
          <dl className="grid grid-cols-[auto_auto] gap-x-4 gap-y-1 sm:justify-end">
            <dt className="text-muted-foreground">Number</dt>
            <dd className="font-medium">{invoice.invoiceNumber}</dd>
            <dt className="text-muted-foreground">Status</dt>
            <dd>
              <StatusBadge status={invoice.status} isOverdue={invoice.isOverdue} />
            </dd>
            <dt className="text-muted-foreground">Issued</dt>
            <dd>{formatDate(invoice.issueDate)}</dd>
            <dt className="text-muted-foreground">Due</dt>
            <dd>{formatDate(invoice.dueDate)}</dd>
          </dl>
        </div>
      </header>

      <section className="mt-8 space-y-1">
        <h2 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Bill to
        </h2>
        <p className="font-medium">{invoice.client.name}</p>
        {invoice.client.company ? <p>{invoice.client.company}</p> : null}
        {invoice.client.address ? (
          <p className="whitespace-pre-line">{invoice.client.address}</p>
        ) : null}
        <p className="text-muted-foreground">{invoice.client.email}</p>
      </section>

      <div className="mt-8 overflow-x-auto">
        <table className="w-full min-w-[32rem]">
          <thead>
            <tr className="border-b-2 border-foreground text-left">
              <th className="py-2 font-semibold">Description</th>
              <th className="py-2 text-right font-semibold">Qty</th>
              <th className="py-2 text-right font-semibold">Unit price</th>
              <th className="py-2 text-right font-semibold">Amount</th>
            </tr>
          </thead>
          <tbody>
            {invoice.items.map((item) => (
              <tr key={item.id} className="border-b align-top">
                <td className="py-2 pr-4 whitespace-pre-line">{item.description}</td>
                <td className="py-2 text-right tabular-nums">{formatQuantity(item.quantity)}</td>
                <td className="py-2 text-right tabular-nums">{money(item.unitPrice)}</td>
                <td className="py-2 text-right tabular-nums">{money(item.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <dl className="mt-4 ml-auto grid max-w-xs grid-cols-2 gap-x-6 gap-y-1">
        <dt className="text-muted-foreground">Subtotal</dt>
        <dd className="text-right tabular-nums">{money(invoice.subtotal)}</dd>
        <dt className="text-muted-foreground">Tax ({formatQuantity(invoice.taxRate)}%)</dt>
        <dd className="text-right tabular-nums">{money(invoice.taxAmount)}</dd>
        <dt className="border-t border-foreground pt-1 font-semibold">Total</dt>
        <dd className="border-t border-foreground pt-1 text-right font-semibold tabular-nums">
          {money(invoice.total)}
        </dd>
        {hasPayment ? (
          <>
            <dt className="text-muted-foreground">Amount paid</dt>
            <dd className="text-right tabular-nums">{money(invoice.amountPaid)}</dd>
            <dt className="font-semibold">Balance due</dt>
            <dd className="text-right font-semibold tabular-nums">{money(invoice.balanceDue)}</dd>
          </>
        ) : null}
      </dl>

      {invoice.notes ? (
        <section className="mt-8 space-y-1">
          <h2 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Notes
          </h2>
          <p className="whitespace-pre-line">{invoice.notes}</p>
        </section>
      ) : null}
    </article>
  );
}
