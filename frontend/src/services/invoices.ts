import type {
  Invoice,
  InvoiceAction,
  InvoiceInput,
  InvoiceListItem,
  InvoiceStatusFilter,
  Page,
} from "@/types/api";

import { API_PREFIX, api, apiDownload } from "./api";

export interface InvoiceListParams {
  status?: InvoiceStatusFilter;
  clientId?: number;
  page?: number;
  pageSize?: number;
}

function query(params: InvoiceListParams): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.clientId) search.set("clientId", String(params.clientId));
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const invoicesService = {
  list: (params: InvoiceListParams = {}): Promise<Page<InvoiceListItem>> =>
    api.get<Page<InvoiceListItem>>(`${API_PREFIX}/invoices${query(params)}`),
  get: (id: number): Promise<Invoice> => api.get<Invoice>(`${API_PREFIX}/invoices/${id}`),
  create: (input: InvoiceInput): Promise<Invoice> =>
    api.post<Invoice>(`${API_PREFIX}/invoices`, input),
  update: (id: number, input: InvoiceInput): Promise<Invoice> =>
    api.put<Invoice>(`${API_PREFIX}/invoices/${id}`, input),
  remove: (id: number): Promise<null> => api.delete(`${API_PREFIX}/invoices/${id}`),
  act: (id: number, action: InvoiceAction): Promise<Invoice> =>
    api.post<Invoice>(`${API_PREFIX}/invoices/${id}/${action}`),
  downloadPdf: (id: number) => apiDownload(`${API_PREFIX}/invoices/${id}/pdf`),
};
