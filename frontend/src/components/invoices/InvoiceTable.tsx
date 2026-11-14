import { Link } from "react-router";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/format";
import { formatMoney } from "@/lib/money";
import type { InvoiceListItem } from "@/types/api";

import { StatusBadge } from "./StatusBadge";

interface InvoiceTableProps {
  invoices: InvoiceListItem[];
  showClient?: boolean;
}

export function InvoiceTable({ invoices, showClient = true }: InvoiceTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Number</TableHead>
          {showClient ? <TableHead>Client</TableHead> : null}
          <TableHead>Issued</TableHead>
          <TableHead>Due</TableHead>
          <TableHead className="text-right">Total</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.id}>
            <TableCell className="font-medium">
              <Link to={`/invoices/${invoice.id}`} className="hover:underline">
                {invoice.invoiceNumber}
              </Link>
            </TableCell>
            {showClient ? <TableCell>{invoice.clientName}</TableCell> : null}
            <TableCell>{formatDate(invoice.issueDate)}</TableCell>
            <TableCell>{formatDate(invoice.dueDate)}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(invoice.total, invoice.currency)}
            </TableCell>
            <TableCell>
              <StatusBadge status={invoice.status} isOverdue={invoice.isOverdue} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
