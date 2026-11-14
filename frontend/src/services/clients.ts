import type { Client, ClientDetail, ClientInput, Page } from "@/types/api";

import { API_PREFIX, api } from "./api";

export interface ClientListParams {
  q?: string;
  page?: number;
  pageSize?: number;
}

function query(params: ClientListParams): string {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const clientsService = {
  list: (params: ClientListParams = {}): Promise<Page<Client>> =>
    api.get<Page<Client>>(`${API_PREFIX}/clients${query(params)}`),
  get: (id: number): Promise<ClientDetail> => api.get<ClientDetail>(`${API_PREFIX}/clients/${id}`),
  create: (input: ClientInput): Promise<ClientDetail> =>
    api.post<ClientDetail>(`${API_PREFIX}/clients`, input),
  update: (id: number, input: ClientInput): Promise<ClientDetail> =>
    api.put<ClientDetail>(`${API_PREFIX}/clients/${id}`, input),
  remove: (id: number): Promise<null> => api.delete(`${API_PREFIX}/clients/${id}`),
};
