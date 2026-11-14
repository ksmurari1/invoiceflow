import { Plus, UserPlus } from "lucide-react";
import { Link } from "react-router";

import { EmptyState, ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { InvoiceTable } from "@/components/invoices/InvoiceTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboard } from "@/hooks/useDashboard";
import { useMe } from "@/hooks/useMe";
import { formatMoney } from "@/lib/money";
import { cn } from "@/lib/utils";
import type { Bucket, Currency, CurrencySummary } from "@/types/api";

interface StatCardProps {
  label: string;
  bucket: Bucket;
  currency: Currency;
  hint: string;
  tone?: "default" | "danger" | "success";
}

function StatCard({ label, bucket, currency, hint, tone = "default" }: StatCardProps) {
  return (
    <Card className="gap-2">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle
          className={cn(
            "text-2xl tabular-nums",
            tone === "danger" && bucket.count > 0 && "text-red-600 dark:text-red-400",
            tone === "success" && "text-green-700 dark:text-green-400",
          )}
        >
          {formatMoney(bucket.amount, currency)}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        {bucket.count} {bucket.count === 1 ? "invoice" : "invoices"} · {hint}
      </CardContent>
    </Card>
  );
}

function CurrencyStats({ summary, showHeading }: { summary: CurrencySummary; showHeading: boolean }) {
  return (
    <section className="space-y-3" aria-label={`${summary.currency} totals`}>
      {showHeading ? <h2 className="text-sm font-medium">{summary.currency}</h2> : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Outstanding"
          bucket={summary.outstanding}
          currency={summary.currency}
          hint="sent, unpaid"
        />
        <StatCard
          label="Overdue"
          bucket={summary.overdue}
          currency={summary.currency}
          hint="past due date"
          tone="danger"
        />
        <StatCard
          label="Paid"
          bucket={summary.paid}
          currency={summary.currency}
          hint="all time"
          tone="success"
        />
        <StatCard
          label="Drafts"
          bucket={summary.draft}
          currency={summary.currency}
          hint="not sent yet"
        />
      </div>
    </section>
  );
}

const EMPTY: Bucket = { count: 0, amount: "0.00" };

export function DashboardPage() {
  const { data, isPending, error } = useDashboard();
  const me = useMe();

  const actions = (
    <>
      <Button asChild>
        <Link to="/invoices/new">
          <Plus /> New invoice
        </Link>
      </Button>
      <Button asChild variant="outline">
        <Link to="/clients/new">
          <UserPlus /> New client
        </Link>
      </Button>
    </>
  );

  if (error) return <ErrorAlert error={error} title="Could not load the dashboard" />;
  if (isPending) return <LoadingState />;

  const currencies: CurrencySummary[] =
    data.currencies.length > 0
      ? data.currencies
      : [
          {
            currency: me.data?.defaultCurrency ?? "USD",
            draft: EMPTY,
            outstanding: EMPTY,
            overdue: EMPTY,
            paid: EMPTY,
          },
        ];

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <PageHeader
        title="Dashboard"
        description={`${data.clientCount} ${data.clientCount === 1 ? "client" : "clients"} · ${data.invoiceCount} ${data.invoiceCount === 1 ? "invoice" : "invoices"}`}
        actions={actions}
      />

      {data.clientCount === 0 ? (
        <EmptyState
          title="Welcome to InvoiceFlow"
          description="Start by adding a client, then create your first invoice."
          action={
            <Button asChild>
              <Link to="/clients/new">
                <UserPlus /> Add your first client
              </Link>
            </Button>
          }
        />
      ) : null}

      <div className="space-y-6">
        {currencies.map((summary) => (
          <CurrencyStats
            key={summary.currency}
            summary={summary}
            showHeading={currencies.length > 1}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent invoices</CardTitle>
        </CardHeader>
        <CardContent className="px-2">
          {data.recentInvoices.length === 0 ? (
            <p className="px-4 text-sm text-muted-foreground">No invoices yet.</p>
          ) : (
            <InvoiceTable invoices={data.recentInvoices} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
