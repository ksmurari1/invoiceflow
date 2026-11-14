import { Link, useNavigate, useParams, useSearchParams } from "react-router";

import { EmptyState, ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { InvoiceForm } from "@/components/invoices/InvoiceForm";
import { invoiceToValues, newInvoiceValues } from "@/components/invoices/invoiceFormModel";
import { Button } from "@/components/ui/button";
import { useClientList } from "@/hooks/useClients";
import { useInvoice, useSaveInvoice } from "@/hooks/useInvoices";
import { useMe } from "@/hooks/useMe";

const CLIENT_PICKER_LIMIT = 100;

/** Create (/invoices/new[?clientId=]) or edit a draft (/invoices/:id/edit). */
export function InvoiceFormPage() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const id = params.id ? Number(params.id) : undefined;

  const me = useMe();
  const clients = useClientList({ pageSize: CLIENT_PICKER_LIMIT });
  const existing = useInvoice(id ?? 0);
  const save = useSaveInvoice(id);

  const loading = me.isPending || clients.isPending || (id !== undefined && existing.isPending);
  const loadError = me.error ?? clients.error ?? (id !== undefined ? existing.error : null);

  if (loadError) return <ErrorAlert error={loadError} title="Could not load the invoice form" />;
  if (loading || !me.data || !clients.data) return <LoadingState />;

  if (clients.data.total === 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title="New invoice" />
        <EmptyState
          title="Add a client first"
          description="Every invoice is billed to a client."
          action={
            <Button asChild>
              <Link to="/clients/new">Add client</Link>
            </Button>
          }
        />
      </div>
    );
  }

  if (existing.data && existing.data.status !== "draft") {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title={`Edit ${existing.data.invoiceNumber}`} />
        <EmptyState
          title="Only draft invoices can be edited."
          description={`This invoice is ${existing.data.status}.`}
          action={
            <Button asChild variant="outline">
              <Link to={`/invoices/${existing.data.id}`}>Back to invoice</Link>
            </Button>
          }
        />
      </div>
    );
  }

  const initialValues = existing.data
    ? invoiceToValues(existing.data)
    : newInvoiceValues({
        clientId: searchParams.get("clientId") ?? undefined,
        currency: me.data.defaultCurrency,
        taxRate: me.data.defaultTaxRate,
      });

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title={existing.data ? `Edit ${existing.data.invoiceNumber}` : "New invoice"}
        description="Totals are previewed here and calculated exactly by the server when you save."
      />
      <InvoiceForm
        key={existing.data?.id ?? "new"}
        clients={clients.data.items}
        initialValues={initialValues}
        submitLabel={existing.data ? "Save changes" : "Create invoice"}
        submitting={save.isPending}
        serverError={save.error}
        onSubmit={(input) =>
          save.mutate(input, { onSuccess: (invoice) => navigate(`/invoices/${invoice.id}`) })
        }
        onCancel={() => navigate(id ? `/invoices/${id}` : "/invoices")}
      />
    </div>
  );
}
