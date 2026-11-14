/**
 * Shared API types. They mirror the backend schemas: camelCase JSON, money and quantities
 * as decimal strings, one error envelope.
 */

/** A decimal number serialized as a string, e.g. "1250.00". Never convert to a JS number. */
export type DecimalString = string;

/** ISO date "YYYY-MM-DD". */
export type IsoDate = string;

export interface ApiErrorField {
  field: string;
  message: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    fields: ApiErrorField[];
  };
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
}

export type Currency = "USD" | "EUR" | "GBP" | "CAD" | "AUD" | "INR";

export interface User {
  id: number;
  email: string;
  fullName: string | null;
  businessName: string | null;
  businessAddress: string | null;
  defaultCurrency: Currency;
  defaultTaxRate: DecimalString;
}

// --- Clients ---------------------------------------------------------------------------------

export interface Client {
  id: number;
  name: string;
  email: string;
  company: string | null;
  address: string | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ClientDetail extends Client {
  invoiceCount: number;
}

export interface ClientInput {
  name: string;
  email: string;
  company: string | null;
  address: string | null;
  notes: string | null;
}

// --- Invoices --------------------------------------------------------------------------------

export type InvoiceStatus = "draft" | "sent" | "paid" | "void";
export type InvoiceStatusFilter = InvoiceStatus | "overdue";

export interface InvoiceItem {
  id: number;
  description: string;
  quantity: DecimalString;
  unitPrice: DecimalString;
  amount: DecimalString;
  position: number;
}

export interface InvoiceClient {
  id: number;
  name: string;
  email: string;
  company: string | null;
  address: string | null;
}

export interface Invoice {
  id: number;
  invoiceNumber: string;
  clientId: number;
  client: InvoiceClient;
  status: InvoiceStatus;
  isOverdue: boolean;
  issueDate: IsoDate;
  dueDate: IsoDate;
  currency: Currency;
  subtotal: DecimalString;
  taxRate: DecimalString;
  taxAmount: DecimalString;
  total: DecimalString;
  amountPaid: DecimalString;
  balanceDue: DecimalString;
  notes: string | null;
  sentAt: string | null;
  paidAt: string | null;
  createdAt: string;
  updatedAt: string;
  items: InvoiceItem[];
}

export interface InvoiceListItem {
  id: number;
  invoiceNumber: string;
  clientId: number;
  clientName: string;
  status: InvoiceStatus;
  isOverdue: boolean;
  issueDate: IsoDate;
  dueDate: IsoDate;
  currency: Currency;
  total: DecimalString;
  amountPaid: DecimalString;
  balanceDue: DecimalString;
}

export interface InvoiceItemInput {
  description: string;
  quantity: DecimalString;
  unitPrice: DecimalString;
}

/** Request body for creating/replacing a draft. Totals are always computed by the server. */
export interface InvoiceInput {
  clientId: number;
  issueDate: IsoDate;
  dueDate: IsoDate;
  currency: Currency;
  taxRate: DecimalString;
  notes: string | null;
  items: InvoiceItemInput[];
}

export type InvoiceAction = "send" | "mark-paid" | "void";

// --- Dashboard -------------------------------------------------------------------------------

export interface Bucket {
  count: number;
  amount: DecimalString;
}

export interface CurrencySummary {
  currency: Currency;
  draft: Bucket;
  outstanding: Bucket;
  overdue: Bucket;
  paid: Bucket;
}

export interface DashboardSummary {
  clientCount: number;
  invoiceCount: number;
  currencies: CurrencySummary[];
  recentInvoices: InvoiceListItem[];
}
