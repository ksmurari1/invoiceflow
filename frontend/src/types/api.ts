/**
 * Shared API types. They mirror the backend contract in PRPs/invoiceflow-mvp-plan.md:
 * camelCase JSON, money as decimal strings, a single error envelope.
 */

/** A decimal number serialized as a string, e.g. "1250.00". Never convert to a JS number. */
export type DecimalString = string;

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
