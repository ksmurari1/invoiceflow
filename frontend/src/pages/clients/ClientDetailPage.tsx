import { Pencil, Plus, Trash2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";

import { ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { InvoiceTable } from "@/components/invoices/InvoiceTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useClient, useDeleteClient } from "@/hooks/useClients";
import { useInvoiceList } from "@/hooks/useInvoices";

export function ClientDetailPage() {
  const id = Number(useParams().id);
  const navigate = useNavigate();
  const { data: client, isPending, error } = useClient(id);
  const invoices = useInvoiceList({ clientId: id, pageSize: 50 });
  const remove = useDeleteClient();

  if (isPending) return <LoadingState />;
  if (error || !client) return <ErrorAlert error={error} title="Could not load client" />;

  const handleDelete = () => {
    const drafts = client.invoiceCount > 0 ? " Its draft invoices will be deleted too." : "";
    if (!window.confirm(`Delete ${client.name}?${drafts}`)) return;
    remove.mutate(client.id, { onSuccess: () => navigate("/clients") });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title={client.name}
        description={client.company ?? undefined}
        actions={
          <>
            <Button asChild>
              <Link to={`/invoices/new?clientId=${client.id}`}>
                <Plus /> New invoice
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to={`/clients/${client.id}/edit`}>
                <Pencil /> Edit
              </Link>
            </Button>
            <Button variant="outline" onClick={handleDelete} disabled={remove.isPending}>
              <Trash2 /> Delete
            </Button>
          </>
        }
      />

      {remove.error ? <ErrorAlert error={remove.error} title="Could not delete client" /> : null}

      <Card>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <p className="text-muted-foreground">Email</p>
            <p>{client.email}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Company</p>
            <p>{client.company ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Address</p>
            <p className="whitespace-pre-line">{client.address ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Notes</p>
            <p className="whitespace-pre-line">{client.notes ?? "—"}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invoices ({client.invoiceCount})</CardTitle>
        </CardHeader>
        <CardContent className="px-2">
          {invoices.error ? <ErrorAlert error={invoices.error} /> : null}
          {invoices.data && invoices.data.items.length === 0 ? (
            <p className="px-4 pb-2 text-sm text-muted-foreground">No invoices for this client yet.</p>
          ) : null}
          {invoices.data && invoices.data.items.length > 0 ? (
            <InvoiceTable invoices={invoices.data.items} showClient={false} />
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
