import { Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { EmptyState, ErrorAlert, LoadingState } from "@/components/common/Feedback";
import { PageHeader } from "@/components/common/PageHeader";
import { Pagination } from "@/components/common/Pagination";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useClientList } from "@/hooks/useClients";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";

const PAGE_SIZE = 20;

export function ClientListPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(search.trim());
  const { data, isPending, error } = useClientList({ q, page, pageSize: PAGE_SIZE });

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="Clients"
        description="The people and companies you bill."
        actions={
          <Button asChild>
            <Link to="/clients/new">
              <Plus /> New client
            </Link>
          </Button>
        }
      />

      <div className="relative max-w-sm">
        <Search
          className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground"
          aria-hidden="true"
        />
        <Input
          aria-label="Search clients"
          placeholder="Search by name, email or company"
          className="pl-9"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {error ? <ErrorAlert error={error} title="Could not load clients" /> : null}
      {isPending ? <LoadingState /> : null}

      {data && data.total === 0 ? (
        q ? (
          <EmptyState title="No clients match your search." />
        ) : (
          <EmptyState
            title="No clients yet"
            description="Add your first client to start invoicing."
            action={
              <Button asChild>
                <Link to="/clients/new">
                  <Plus /> Add client
                </Link>
              </Button>
            }
          />
        )
      ) : null}

      {data && data.total > 0 ? (
        <Card className="py-2">
          <CardContent className="px-2">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead className="text-right">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((client) => (
                  <TableRow key={client.id}>
                    <TableCell className="font-medium">
                      <Link to={`/clients/${client.id}`} className="hover:underline">
                        {client.name}
                      </Link>
                    </TableCell>
                    <TableCell>{client.email}</TableCell>
                    <TableCell className="text-muted-foreground">{client.company ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link to={`/invoices/new?clientId=${client.id}`}>New invoice</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {data ? (
        <Pagination
          page={data.page}
          pageSize={data.pageSize}
          total={data.total}
          onPageChange={setPage}
        />
      ) : null}
    </div>
  );
}
