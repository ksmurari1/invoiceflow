import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { InvoiceStatus } from "@/types/api";

const STYLES: Record<InvoiceStatus | "overdue", string> = {
  draft: "bg-secondary text-secondary-foreground",
  sent: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
  overdue: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
  paid: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200",
  void: "bg-transparent text-muted-foreground line-through",
};

const LABELS: Record<InvoiceStatus | "overdue", string> = {
  draft: "Draft",
  sent: "Sent",
  overdue: "Overdue",
  paid: "Paid",
  void: "Void",
};

export function StatusBadge({ status, isOverdue }: { status: InvoiceStatus; isOverdue: boolean }) {
  const key = isOverdue ? "overdue" : status;
  return (
    <Badge variant="outline" className={cn("border-transparent", STYLES[key])}>
      {LABELS[key]}
    </Badge>
  );
}
