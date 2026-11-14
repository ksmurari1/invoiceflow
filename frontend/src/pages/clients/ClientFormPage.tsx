import { useNavigate, useParams } from "react-router";

import { ClientForm } from "@/components/clients/ClientForm";
import { ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { useClient, useSaveClient } from "@/hooks/useClients";

/** Create (/clients/new) or edit (/clients/:id/edit) a client. */
export function ClientFormPage() {
  const params = useParams();
  const id = params.id ? Number(params.id) : undefined;
  const navigate = useNavigate();
  const existing = useClient(id ?? 0);
  const save = useSaveClient(id);

  if (id !== undefined && existing.isPending) return <LoadingState />;
  if (id !== undefined && existing.error) {
    return <ErrorAlert error={existing.error} title="Could not load client" />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title={id ? `Edit ${existing.data?.name ?? "client"}` : "New client"} />
      <Card>
        <CardContent>
          <ClientForm
            initial={existing.data}
            submitLabel={id ? "Save changes" : "Create client"}
            submitting={save.isPending}
            serverError={save.error}
            onSubmit={(input) =>
              save.mutate(input, {
                onSuccess: (client) => navigate(`/clients/${client.id}`),
              })
            }
            onCancel={() => navigate(id ? `/clients/${id}` : "/clients")}
          />
        </CardContent>
      </Card>
    </div>
  );
}
