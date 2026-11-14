import { Ban, CheckCircle2, Download, Pencil, Send, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { InvoicePreview } from "@/components/invoices/InvoicePreview";
import { Button } from "@/components/ui/button";
import { useDeleteInvoice, useInvoice, useInvoiceAction } from "@/hooks/useInvoices";
import { useMe } from "@/hooks/useMe";
import { saveBlob } from "@/lib/download";
import { invoicesService } from "@/services/invoices";
import type { InvoiceAction } from "@/types/api";

export function InvoiceDetailPage() {
  const id = Number(useParams().id);
  const navigate = useNavigate();
  const { data: invoice, isPending, error } = useInvoice(id);
  const me = useMe();
  const action = useInvoiceAction(id);
  const remove = useDeleteInvoice();
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<unknown>(null);

  if (isPending) return <LoadingState />;
  if (error || !invoice) return <ErrorAlert error={error} title="Could not load invoice" />;

  const run = (name: InvoiceAction, confirmText?: string) => {
    if (confirmText && !window.confirm(confirmText)) return;
    action.mutate(name);
  };

  const handleDelete = () => {
    if (!window.confirm(`Delete draft ${invoice.invoiceNumber}? This cannot be undone.`)) return;
    remove.mutate(invoice.id, { onSuccess: () => navigate("/invoices") });
  };

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const { blob, filename } = await invoicesService.downloadPdf(invoice.id);
      saveBlob(blob, filename ?? `${invoice.invoiceNumber}.pdf`);
    } catch (caught) {
      setDownloadError(caught);
    } finally {
      setDownloading(false);
    }
  };

  const busy = action.isPending || remove.isPending;
  const isDraft = invoice.status === "draft";
  const isSent = invoice.status === "sent";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title={invoice.invoiceNumber}
        description={
          <Link to={`/clients/${invoice.clientId}`} className="hover:underline">
            {invoice.client.name}
          </Link>
        }
        actions={
          <>
            <Button onClick={handleDownload} disabled={downloading}>
              <Download /> {downloading ? "Preparing…" : "Download PDF"}
            </Button>
            {isDraft ? (
              <>
                <Button asChild variant="outline">
                  <Link to={`/invoices/${invoice.id}/edit`}>
                    <Pencil /> Edit
                  </Link>
                </Button>
                <Button variant="outline" disabled={busy} onClick={() => run("send")}>
                  <Send /> Mark as sent
                </Button>
              </>
            ) : null}
            {isSent ? (
              <Button variant="outline" disabled={busy} onClick={() => run("mark-paid")}>
                <CheckCircle2 /> Mark as paid
              </Button>
            ) : null}
            {isDraft || isSent ? (
              <Button
                variant="outline"
                disabled={busy}
                onClick={() =>
                  run("void", `Void ${invoice.invoiceNumber}? A void invoice cannot be changed.`)
                }
              >
                <Ban /> Void
              </Button>
            ) : null}
            {isDraft ? (
              <Button variant="outline" disabled={busy} onClick={handleDelete}>
                <Trash2 /> Delete
              </Button>
            ) : null}
          </>
        }
      />

      {action.error ? <ErrorAlert error={action.error} title="Action failed" /> : null}
      {remove.error ? <ErrorAlert error={remove.error} title="Could not delete invoice" /> : null}
      {downloadError ? (
        <ErrorAlert error={downloadError} title="Could not download the PDF" />
      ) : null}

      <InvoicePreview invoice={invoice} seller={me.data} />
    </div>
  );
}
