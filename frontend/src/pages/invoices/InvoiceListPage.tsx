import { Plus } from "lucide-react";
import { Link, useSearchParams } from "react-router";

import { EmptyState, ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { InvoiceTable } from "@/components/invoices/InvoiceTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useInvoiceList } from "@/hooks/useInvoices";
import { cn } from "@/lib/utils";
import type { InvoiceStatusFilter } from "@/types/api";

const PAGE_SIZE = 20;

const TABS: { value: InvoiceStatusFilter | undefined; label: string }[] = [
  { value: undefined, label: "All" },
  { value: "draft", label: "Draft" },
  { value: "sent", label: "Sent" },
  { value: "overdue", label: "Overdue" },
  { value: "paid", label: "Paid" },
  { value: "void", label: "Void" },
];

function parseStatus(value: string | null): InvoiceStatusFilter | undefined {
  return TABS.find((tab) => tab.value === value)?.value;
}

export function InvoiceListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const status = parseStatus(searchParams.get("status"));
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const { data, isPending, error } = useInvoiceList({ status, page, pageSize: PAGE_SIZE });

  const update = (next: { status?: InvoiceStatusFilter; page?: number }) => {
    const params = new URLSearchParams();
    if (next.status) params.set("status", next.status);
    if (next.page && next.page > 1) params.set("page", String(next.page));
    setSearchParams(params);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="Invoices"
        description="Create, track and download your invoices."
        actions={
          <Button asChild>
            <Link to="/invoices/new">
              <Plus /> New invoice
            </Link>
          </Button>
        }
      />

      <div role="tablist" aria-label="Filter by status" className="flex flex-wrap gap-1">
        {TABS.map((tab) => {
          const active = tab.value === status;
          return (
            <button
              key={tab.label}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => update({ status: tab.value })}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {error ? <ErrorAlert error={error} title="Could not load invoices" /> : null}
      {isPending ? <LoadingState /> : null}

      {data && data.total === 0 ? (
        status ? (
          <EmptyState title="No invoices with this status." />
        ) : (
          <EmptyState
            title="No invoices yet"
            description="Create your first invoice in under a minute."
            action={
              <Button asChild>
                <Link to="/invoices/new">
                  <Plus /> New invoice
                </Link>
              </Button>
            }
          />
        )
      ) : null}

      {data && data.total > 0 ? (
        <Card className="py-2">
          <CardContent className="px-2">
            <InvoiceTable invoices={data.items} />
          </CardContent>
        </Card>
      ) : null}

      {data ? (
        <Pagination
          page={data.page}
          pageSize={data.pageSize}
          total={data.total}
          onPageChange={(next) => update({ status, page: next })}
        />
      ) : null}
    </div>
  );
}
